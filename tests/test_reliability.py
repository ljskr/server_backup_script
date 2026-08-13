import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dotenv import load_dotenv

from backup import parse_args
from config_parser import _create_uploader_from_config, _resolve_value, _validate_config
from easybk import EncipherManager, Task, TaskManager, UploadManager, UploadTask, Uploader
from easybk.run_lock import RunLock
from easybk.tasks import PackTask
from easybk.uploaders.ftp_uploader import FTPClient
from easybk.uploaders.oss_uploader import OSSUploader


class StubTask(Task):
    def __init__(self, output_dir, result=True, error=None):
        super().__init__("stub", output_dir)
        self.next_result = result
        self.error = error

    def do_task(self):
        if self.error:
            raise self.error
        return self.next_result


class StubUploader(Uploader):
    def __init__(self, result=True):
        super().__init__("stub-uploader")
        self.next_result = result

    def do_upload(self, task, remote_dir):
        return self.next_result


class ReliabilityTests(unittest.TestCase):
    def test_cli_accepts_custom_paths_and_validation_mode(self):
        args = parse_args([
            "--config", "custom.yaml",
            "--env-file", "secrets.env",
            "--validate-config",
        ])
        self.assertTrue(args.config.endswith("custom.yaml"))
        self.assertTrue(args.env_file.endswith("secrets.env"))
        self.assertTrue(args.validate_config)

    def test_config_rejects_duplicate_names_and_missing_reference(self):
        config = {
            "tasks": [
                {"type": "single_file", "task_name": "same", "output_dir": "out",
                 "source_file": "a", "uploaders": [{"uploader_name": "missing"}]},
                {"type": "single_file", "task_name": "same", "output_dir": "out",
                 "source_file": "b"},
            ],
            "uploaders": [],
        }

        errors = _validate_config(config)

        self.assertIn("任务名称重复: same", errors)
        self.assertTrue(any("不存在的上传器: missing" in error for error in errors))

    def test_config_rejects_deprecated_upload_tasks(self):
        errors = _validate_config({"tasks": [], "uploaders": [], "upload_tasks": []})
        self.assertTrue(any("upload_tasks 已废弃" in error for error in errors))

    def test_unresolved_environment_variable_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "未解析的变量"):
            _resolve_value("${ENV:SECRET_THAT_DOES_NOT_EXIST}", {})

    def test_uploader_credentials_support_environment_variables(self):
        config = {
            "type": "ftp", "name": "ftp", "host": "localhost",
            "username": "${ENV:BACKUP_TEST_USER}", "password": "${ENV:BACKUP_TEST_PASSWORD}",
        }
        with mock.patch.dict(os.environ, {"BACKUP_TEST_USER": "user", "BACKUP_TEST_PASSWORD": "pass"}):
            uploader = _create_uploader_from_config(config)

        self.assertEqual(uploader.username, "user")
        self.assertEqual(uploader.password, "pass")

    def test_task_manager_reports_command_failure(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            state_file = Path(temp_dir) / "state.txt"
            state_file.touch()
            manager = TaskManager()
            manager.set_encipher_file(str(state_file))
            manager.add_task(StubTask(temp_dir, error=RuntimeError("failed")))

            self.assertFalse(manager.run_all_task(use_thread_pool=False))

    def test_digest_state_is_committed_explicitly_after_upload_phase(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            state_file = Path(temp_dir) / "state.txt"
            manager = TaskManager()
            manager.set_encipher_file(str(state_file))
            manager.encipher_manager.load_data_from_file(str(state_file))
            manager.encipher_manager.set_value("source", "digest")

            self.assertFalse(state_file.exists())
            manager.save_state()
            self.assertTrue(state_file.exists())

    def test_upload_manager_reports_upload_failure(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            task = StubTask(temp_dir)
            task.result = True
            manager = UploadManager()
            manager.add_upload_task(UploadTask(task, StubUploader(result=False)))

            self.assertFalse(manager.run_all_upload())

    def test_pack_task_uses_argument_list_and_removes_failed_temp_file(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            task = PackTask("pack", temp_dir, temp_dir, ["file with spaces", "; unsafe"])
            error = subprocess.CalledProcessError(2, "tar")

            with mock.patch("easybk.tasks.pack_task.subprocess.run", side_effect=error) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    task.run()

            command = run.call_args.args[0]
            self.assertEqual(command[:2], ["tar", "zcf"])
            self.assertEqual(command[-2:], ["file with spaces", "; unsafe"])
            self.assertEqual(list(Path(temp_dir).glob("*.tgz")), [])

    @unittest.skipUnless(shutil.which("tar"), "tar is not installed")
    def test_pack_task_creates_verified_archive(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            run_dir = Path(temp_dir) / "source"
            output_dir = Path(temp_dir) / "output"
            run_dir.mkdir()
            output_dir.mkdir()
            (run_dir / "file.txt").write_text("backup content", encoding="utf-8")

            task = PackTask("pack", str(output_dir), str(run_dir), ["file.txt"])

            self.assertTrue(task.run())
            self.assertTrue(Path(task.output_full_path).is_file())

    def test_dotenv_loads_values_without_overriding_environment(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("FROM_FILE='value with spaces'\nEXISTING=file\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"EXISTING": "system"}, clear=False):
                load_dotenv(str(env_file), override=False)
                self.assertEqual(os.environ["FROM_FILE"], "value with spaces")
                self.assertEqual(os.environ["EXISTING"], "system")
            os.environ.pop("FROM_FILE", None)

    def test_digest_state_is_atomic_and_supports_paths_with_spaces(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            state_file = Path(temp_dir) / "digest state.txt"
            manager = EncipherManager()
            manager.load_data_from_file(str(state_file))
            manager.set_value("path with spaces/file.txt", "abc123")
            manager.save_data_to_file()

            manager.load_data_from_file(str(state_file))
            self.assertEqual(manager.file_dict["path with spaces/file.txt"], "abc123")
            self.assertEqual(list(Path(temp_dir).glob(".digest-*")), [])

    def test_sha256_digest(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            source = Path(temp_dir) / "source"
            source.write_bytes(b"abc")
            self.assertEqual(
                EncipherManager.digest(str(source)),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_run_lock_prevents_second_instance_and_cleans_up(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            lock_path = Path(temp_dir) / "backup.lock"
            with RunLock(str(lock_path)):
                self.assertTrue(lock_path.exists())
                with self.assertRaisesRegex(RuntimeError, "已有备份实例"):
                    RunLock(str(lock_path)).acquire()
            self.assertFalse(lock_path.exists())

    def test_run_lock_recovers_stale_pid_file(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            lock_path = Path(temp_dir) / "backup.lock"
            lock_path.write_text("99999999", encoding="ascii")
            with mock.patch.object(RunLock, "_pid_exists", return_value=False):
                with RunLock(str(lock_path)):
                    self.assertEqual(lock_path.read_text(encoding="ascii"), str(os.getpid()))

    def test_ftp_upload_rejects_remote_size_mismatch(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            source = Path(temp_dir) / "source"
            source.write_bytes(b"payload")
            ftp = mock.Mock()
            ftp.size.return_value = 1
            client = FTPClient("host", 21, "user", "pass", mock.Mock())
            client._ftp = ftp
            client._connected = True

            with self.assertRaisesRegex(IOError, "大小校验失败"):
                client.put_file("backup.bin", str(source), retry=1)

    def test_oss_upload_verifies_size_and_promotes_temp_object(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            source = Path(temp_dir) / "source"
            source.write_bytes(b"payload")
            task = StubTask(temp_dir)
            task.output_file_name = "backup.bin"
            task.output_full_path = str(source)
            bucket = mock.Mock()
            bucket.head_object.return_value.content_length = len(b"payload")
            uploader = OSSUploader("oss", "id", "key", "endpoint", "bucket")
            uploader.oss_bucket.get_bucket = mock.Mock(return_value=bucket)

            self.assertTrue(uploader.do_upload(task, "daily"))
            temp_key = bucket.put_object_from_file.call_args.args[0]
            bucket.copy_object.assert_called_once_with("bucket", temp_key, "daily/backup.bin")
            bucket.delete_object.assert_called_once_with(temp_key)

    def test_oss_direct_upload_does_not_copy_or_delete(self):
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            source = Path(temp_dir) / "source"
            source.write_bytes(b"payload")
            task = StubTask(temp_dir)
            task.output_file_name = "backup.bin"
            task.output_full_path = str(source)
            bucket = mock.Mock()
            bucket.head_object.return_value.content_length = len(b"payload")
            uploader = OSSUploader(
                "oss", "id", "key", "endpoint", "bucket", use_temp_object=False)
            uploader.oss_bucket.get_bucket = mock.Mock(return_value=bucket)

            self.assertTrue(uploader.do_upload(task, "daily"))
            bucket.put_object_from_file.assert_called_once_with(
                "daily/backup.bin", str(source))
            bucket.copy_object.assert_not_called()
            bucket.delete_object.assert_not_called()

    def test_oss_temp_object_option_must_be_boolean(self):
        config = {
            "tasks": [],
            "uploaders": [{
                "type": "oss", "name": "oss", "access_id": "id", "access_key": "key",
                "endpoint": "endpoint", "bucket_name": "bucket", "use_temp_object": "false",
            }],
        }
        self.assertTrue(any("use_temp_object 必须是布尔值" in error
                            for error in _validate_config(config)))


if __name__ == "__main__":
    unittest.main()
