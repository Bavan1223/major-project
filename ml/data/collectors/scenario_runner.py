"""
Scenario Runner — Executes controlled behavioral scenarios and generates Common Events.

This module translates scenario definitions into actual system activity
(file operations, process events, network connections) and captures the
resulting Common Events for ML dataset collection.

SAFETY:
    - All file operations restricted to TARGET_DIR
    - No real encryption
    - No destructive operations outside test directory
    - No real ransomware execution

USAGE:
    On the Ubuntu lab machine (~/ransomware-lab/):
    
    from ml.data.collectors.scenario_runner import ScenarioRunner
    runner = ScenarioRunner(target_dir="~/ransomware-lab/test-files/")
    events = runner.run_scenario(scenario_definition, variation)
"""

import os
import time
import random
import string
import uuid
from datetime import datetime, timezone


# Default target directory (Ubuntu lab)
DEFAULT_TARGET_DIR = os.path.expanduser("~/ransomware-lab/test-files/")


class ScenarioRunner:
    """
    Executes behavioral scenarios and captures Common Events.
    
    Each scenario produces a list of Common Events in the standard format
    expected by core/feature_extractor.py.
    """

    def __init__(self, target_dir=None):
        """
        Initialize the scenario runner.
        
        Args:
            target_dir: Directory for file operations. Must exist.
                        Defaults to ~/ransomware-lab/test-files/
        """
        self.target_dir = target_dir or DEFAULT_TARGET_DIR
        self.target_dir = os.path.expanduser(self.target_dir)
        self.events = []
        self._generated_files = []

    def run_scenario(self, scenario, variation=None, seed=None):
        """
        Execute a scenario and return generated Common Events.
        
        Args:
            scenario: Scenario dict from normal_scenarios.json or ransomware_like_scenarios.json
            variation: Optional specific variation dict to use
            seed: Random seed for reproducibility
            
        Returns:
            list: Common Events generated during scenario execution
        """
        self.events = []
        self._generated_files = []

        # Set seed for reproducibility
        if seed is not None:
            random.seed(seed)

        # Resolve parameters from variation or scenario defaults
        params = self._resolve_params(scenario, variation)

        # Dispatch to execution method
        method = scenario["execution"]["method"]
        dispatch = {
            "sleep": self._exec_sleep,
            "sequential_file_modify": self._exec_sequential_file_modify,
            "sequential_mixed_file_ops": self._exec_sequential_mixed_file_ops,
            "mixed_directory_ops": self._exec_mixed_directory_ops,
            "rapid_file_creation_with_processes": self._exec_rapid_creation_with_processes,
            "network_connections_with_minimal_files": self._exec_network_with_minimal_files,
            "network_then_file_create": self._exec_network_then_file_create,
            "repeated_single_file_modify": self._exec_repeated_single_file_modify,
            "interleaved_multi_source": self._exec_interleaved_multi_source,
            "rapid_batch_create": self._exec_rapid_batch_create,
            "rapid_unique_file_modify": self._exec_rapid_unique_file_modify,
            "modify_then_rename": self._exec_modify_then_rename,
            "create_new_then_delete_original": self._exec_create_delete,
            "random_mixed_file_burst": self._exec_random_mixed_burst,
            "slow_unique_file_modify": self._exec_slow_unique_file_modify,
            "multi_process_file_modify": self._exec_multi_process_file_modify,
            "interleaved_network_and_file_modify": self._exec_interleaved_network_file,
            "interleaved_all_sources": self._exec_interleaved_all,
            "rapid_bulk_rename": self._exec_rapid_bulk_rename,
        }

        executor = dispatch.get(method)
        if executor is None:
            raise ValueError(f"Unknown execution method: {method}")

        executor(params)
        return self.events

    def prepare_test_files(self, count, extensions=None):
        """
        Create disposable test files before running a scenario.
        
        Args:
            count: Number of files to create
            extensions: List of extensions to use (cycles through them)
            
        Returns:
            list: Paths to created test files
        """
        extensions = extensions or [".txt"]
        files = []

        os.makedirs(self.target_dir, exist_ok=True)

        for i in range(count):
            ext = extensions[i % len(extensions)]
            filename = f"testfile_{uuid.uuid4().hex[:8]}{ext}"
            filepath = os.path.join(self.target_dir, filename)
            with open(filepath, "w") as f:
                f.write(f"Test content for {filename}\n" * 5)
            files.append(filepath)
            self._generated_files.append(filepath)

        return files

    def cleanup(self):
        """Remove all generated test files."""
        for f in self._generated_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
        self._generated_files = []

    # =========================================================================
    # EVENT GENERATION HELPERS
    # =========================================================================

    def _emit_event(self, source, event_type, indicator=None, pid=None,
                    process=None, data=None):
        """Create and record a Common Event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "event_type": event_type,
            "pid": pid or os.getpid(),
            "process": process or "python3",
            "indicator": indicator,
            "data": data or {},
        }
        self.events.append(event)
        return event

    def _emit_file_event(self, event_type, filepath, indicator=None):
        """Emit a file monitor event."""
        return self._emit_event(
            source="file_monitor",
            event_type=event_type,
            indicator=indicator or f"file_{event_type.split('_')[-1]}",
            data={"path": filepath},
        )

    def _emit_process_event(self, event_type="process_started", process_name=None,
                            pid=None):
        """Emit a process monitor event."""
        return self._emit_event(
            source="process_monitor",
            event_type=event_type,
            indicator="process_activity",
            pid=pid or random.randint(1000, 65000),
            process=process_name or random.choice(["bash", "python3", "cat", "cp", "mv"]),
            data={},
        )

    def _emit_network_event(self, remote_ip=None, remote_port=None, status="ESTABLISHED"):
        """Emit a network monitor event."""
        if remote_ip is None:
            remote_ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        if remote_port is None:
            remote_port = random.choice([80, 443, 8080, 8443, 3000, 5000])
        return self._emit_event(
            source="network_monitor",
            event_type="network_connection",
            indicator="new_established_connection",
            data={
                "local_address": f"192.168.74.131:{random.randint(30000, 60000)}",
                "remote_address": f"{remote_ip}:{remote_port}",
                "status": status,
            },
        )

    # =========================================================================
    # PARAMETER RESOLUTION
    # =========================================================================

    def _resolve_params(self, scenario, variation):
        """Merge scenario defaults with variation overrides."""
        params = dict(scenario.get("parameters", {}))
        if variation:
            params.update(variation)
        return params

    def _get_count(self, params, key, range_key=None):
        """Get a count from params, resolving range if needed."""
        if key in params:
            return params[key]
        if range_key and range_key in params:
            rng = params[range_key]
            return random.randint(rng[0], rng[1])
        return 0

    def _get_delay(self, params):
        """Get delay in seconds from params."""
        if "delay_ms" in params:
            return params["delay_ms"] / 1000.0
        if "delay_between_ops_ms_range" in params:
            rng = params["delay_between_ops_ms_range"]
            return random.randint(rng[0], rng[1]) / 1000.0
        return 0.1

    # =========================================================================
    # EXECUTION METHODS — NORMAL SCENARIOS
    # =========================================================================

    def _exec_sleep(self, params):
        """N1: No activity — just wait."""
        duration = params.get("duration_seconds", 15)
        time.sleep(duration)

    def _exec_sequential_file_modify(self, params):
        """N2: Modify files sequentially with pauses."""
        count = self._get_count(params, "file_count", "file_count_range")
        extensions = params.get("target_extensions", [".txt"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            with open(f, "a") as fp:
                fp.write(f"Modified at {datetime.now().isoformat()}\n")
            self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params))

    def _exec_sequential_mixed_file_ops(self, params):
        """N3: Edit multiple files, occasionally create new ones."""
        count = self._get_count(params, "file_count", "file_count_range")
        create_prob = params.get("create_probability", 0.15)
        extensions = params.get("target_extensions", [".txt", ".py"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            if random.random() < create_prob:
                new_file = os.path.join(self.target_dir, f"new_{uuid.uuid4().hex[:6]}.py")
                with open(new_file, "w") as fp:
                    fp.write("# New file\n")
                self._generated_files.append(new_file)
                self._emit_file_event("file_created", new_file)
            else:
                with open(f, "a") as fp:
                    fp.write(f"Edit at {datetime.now().isoformat()}\n")
                self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params))

    def _exec_mixed_directory_ops(self, params):
        """N4: Create, rename, and delete files (directory organization)."""
        create_count = self._get_count(params, "create_count", "create_count_range")
        rename_count = self._get_count(params, "rename_count", "rename_count_range")
        delete_count = self._get_count(params, "delete_count", "delete_count_range")
        extensions = params.get("target_extensions", [".txt", ".tmp"])

        # Create files
        created_files = []
        for i in range(create_count):
            ext = extensions[i % len(extensions)]
            filepath = os.path.join(self.target_dir, f"dir_file_{uuid.uuid4().hex[:6]}{ext}")
            with open(filepath, "w") as f:
                f.write("Directory organization file\n")
            self._generated_files.append(filepath)
            created_files.append(filepath)
            self._emit_file_event("file_created", filepath)
            time.sleep(self._get_delay(params))

        # Rename some
        for i in range(min(rename_count, len(created_files))):
            old_path = created_files[i]
            new_path = old_path + ".renamed"
            os.rename(old_path, new_path)
            self._generated_files.append(new_path)
            self._emit_file_event("file_renamed", new_path)
            created_files[i] = new_path
            time.sleep(self._get_delay(params))

        # Delete some
        for i in range(min(delete_count, len(created_files))):
            target = created_files[-(i + 1)]
            if os.path.exists(target):
                os.remove(target)
                self._emit_file_event("file_deleted", target)
            time.sleep(self._get_delay(params))

    def _exec_rapid_creation_with_processes(self, params):
        """N5: Rapid file creation with process events (build simulation)."""
        file_count = self._get_count(params, "file_count", "file_create_count_range")
        process_count = self._get_count(params, "process_count", "process_event_count_range")
        extensions = params.get("target_extensions", [".o", ".pyc", ".tmp"])

        # Interleave process events with file creations
        process_interval = max(1, file_count // process_count) if process_count > 0 else file_count + 1

        for i in range(file_count):
            if i % process_interval == 0 and process_count > 0:
                self._emit_process_event("process_started", "gcc")
                process_count -= 1

            ext = extensions[i % len(extensions)]
            filepath = os.path.join(self.target_dir, f"build_{uuid.uuid4().hex[:6]}{ext}")
            with open(filepath, "w") as f:
                f.write(os.urandom(64).hex())
            self._generated_files.append(filepath)
            self._emit_file_event("file_created", filepath)
            time.sleep(self._get_delay(params))

    def _exec_network_with_minimal_files(self, params):
        """N6: Network browsing — many connections, few files."""
        connections = self._get_count(params, "connections", "connection_count_range")
        ip_count = self._get_count(params, "ips", "unique_ip_count_range")
        file_count = self._get_count(params, "files", "file_create_count_range")

        # Generate IPs
        ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
               for _ in range(ip_count)]

        for i in range(connections):
            ip = ips[i % len(ips)]
            self._emit_network_event(remote_ip=ip)
            time.sleep(self._get_delay(params))

        # Minimal file activity
        for i in range(file_count):
            filepath = os.path.join(self.target_dir, f"cache_{uuid.uuid4().hex[:6]}.tmp")
            with open(filepath, "w") as f:
                f.write("cache data")
            self._generated_files.append(filepath)
            self._emit_file_event("file_created", filepath)

    def _exec_network_then_file_create(self, params):
        """N7: Download pattern — network connection then file creation."""
        downloads = self._get_count(params, "downloads", "download_count_range")
        ip_count = self._get_count(params, "ips", "unique_ip_range")
        extensions = params.get("target_extensions", [".pdf", ".zip"])

        ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
               for _ in range(ip_count)]

        for i in range(downloads):
            ip = ips[i % len(ips)]
            self._emit_network_event(remote_ip=ip)
            time.sleep(self._get_delay(params) * 0.3)

            ext = extensions[i % len(extensions)]
            filepath = os.path.join(self.target_dir, f"download_{uuid.uuid4().hex[:6]}{ext}")
            with open(filepath, "w") as f:
                f.write(os.urandom(128).hex())
            self._generated_files.append(filepath)
            self._emit_file_event("file_created", filepath)
            time.sleep(self._get_delay(params) * 0.7)

    def _exec_repeated_single_file_modify(self, params):
        """N8: Log rotation — modify same file(s) repeatedly."""
        write_count = self._get_count(params, "writes", "write_count_range")
        unique_files = self._get_count(params, "unique_files", "unique_file_count")
        if isinstance(unique_files, list):
            unique_files = random.randint(unique_files[0], unique_files[1])
        extensions = params.get("target_extensions", [".log"])

        files = self.prepare_test_files(unique_files, extensions)

        for i in range(write_count):
            target = files[i % len(files)]
            with open(target, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] Log entry {i}\n")
            self._emit_file_event("file_modified", target)
            time.sleep(self._get_delay(params))

    def _exec_interleaved_multi_source(self, params):
        """N9: Mixed high activity — file + process + network interleaved."""
        file_mod = self._get_count(params, "file_mod", "file_modify_count_range")
        file_create = self._get_count(params, "file_create", "file_create_count_range")
        processes = self._get_count(params, "process", "process_event_count_range")
        network = self._get_count(params, "network", "network_event_count_range")
        ip_count = self._get_count(params, "ips", "unique_ip_range") or 2

        extensions = [".py", ".txt", ".cfg"]
        files = self.prepare_test_files(file_mod, extensions)
        ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
               for _ in range(ip_count)]

        # Build operation queue and shuffle
        ops = (
            [("file_modify", f) for f in files] +
            [("file_create", None) for _ in range(file_create)] +
            [("process", None) for _ in range(processes)] +
            [("network", None) for _ in range(network)]
        )
        random.shuffle(ops)

        for op_type, arg in ops:
            if op_type == "file_modify":
                with open(arg, "a") as f:
                    f.write(f"Edit {datetime.now().isoformat()}\n")
                self._emit_file_event("file_modified", arg)
            elif op_type == "file_create":
                fp = os.path.join(self.target_dir, f"mixed_{uuid.uuid4().hex[:6]}.txt")
                with open(fp, "w") as f:
                    f.write("new file\n")
                self._generated_files.append(fp)
                self._emit_file_event("file_created", fp)
            elif op_type == "process":
                self._emit_process_event()
            elif op_type == "network":
                self._emit_network_event(remote_ip=ips[random.randint(0, len(ips)-1)])
            time.sleep(self._get_delay(params))

    def _exec_rapid_batch_create(self, params):
        """N10: Rapid batch file creation (archive extraction)."""
        count = self._get_count(params, "file_count", "file_create_count_range")
        extensions = params.get("target_extensions", [".txt", ".html", ".css", ".js"])

        for i in range(count):
            ext = extensions[i % len(extensions)]
            filepath = os.path.join(self.target_dir, f"extracted_{uuid.uuid4().hex[:6]}{ext}")
            with open(filepath, "w") as f:
                f.write(f"File content {i}\n" * 3)
            self._generated_files.append(filepath)
            self._emit_file_event("file_created", filepath)
            time.sleep(self._get_delay(params))

    # =========================================================================
    # EXECUTION METHODS — RANSOMWARE-LIKE SCENARIOS
    # =========================================================================

    def _exec_rapid_unique_file_modify(self, params):
        """R1/R2: Rapidly modify many unique files."""
        count = self._get_count(params, "file_count", "file_count_range")
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))  # Write random bytes (simulated encryption)
            self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params))

    def _exec_modify_then_rename(self, params):
        """R3: Modify file then rename with ransomware extension."""
        count = self._get_count(params, "file_count", "file_count_range")
        extension = params.get("extension", ".encrypted")
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            # Modify (simulate encryption)
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params) * 0.3)

            # Rename with suspicious extension
            new_path = f + extension
            os.rename(f, new_path)
            self._generated_files.append(new_path)
            self._emit_file_event("file_renamed", new_path)
            time.sleep(self._get_delay(params) * 0.7)

    def _exec_create_delete(self, params):
        """R4: Create encrypted copy, delete original."""
        count = self._get_count(params, "file_count", "file_count_range")
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            # Create "encrypted" copy
            enc_path = f + ".enc"
            with open(enc_path, "wb") as fp:
                fp.write(os.urandom(128))
            self._generated_files.append(enc_path)
            self._emit_file_event("file_created", enc_path)
            time.sleep(self._get_delay(params) * 0.3)

            # Delete original
            os.remove(f)
            self._emit_file_event("file_deleted", f)
            time.sleep(self._get_delay(params) * 0.7)

    def _exec_random_mixed_burst(self, params):
        """R5: Random mix of all file operation types."""
        total_ops = self._get_count(params, "total_ops", "total_ops_range")
        op_mix = params.get("operation_mix", {
            "file_created": 0.20, "file_modified": 0.40,
            "file_deleted": 0.20, "file_renamed": 0.20
        })
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])

        # Prepare enough files for modifications/renames/deletes
        files = self.prepare_test_files(total_ops, extensions)
        file_idx = 0

        for _ in range(total_ops):
            r = random.random()
            cumulative = 0
            chosen_op = "file_modified"
            for op, prob in op_mix.items():
                cumulative += prob
                if r <= cumulative:
                    chosen_op = op
                    break

            if chosen_op == "file_created":
                fp = os.path.join(self.target_dir, f"burst_{uuid.uuid4().hex[:6]}.tmp")
                with open(fp, "w") as f:
                    f.write(os.urandom(64).hex())
                self._generated_files.append(fp)
                self._emit_file_event("file_created", fp)
            elif chosen_op == "file_modified" and file_idx < len(files):
                target = files[file_idx]
                if os.path.exists(target):
                    with open(target, "wb") as f:
                        f.write(os.urandom(64))
                    self._emit_file_event("file_modified", target)
                file_idx += 1
            elif chosen_op == "file_deleted" and file_idx < len(files):
                target = files[file_idx]
                if os.path.exists(target):
                    os.remove(target)
                    self._emit_file_event("file_deleted", target)
                file_idx += 1
            elif chosen_op == "file_renamed" and file_idx < len(files):
                target = files[file_idx]
                if os.path.exists(target):
                    new_path = target + ".locked"
                    os.rename(target, new_path)
                    self._generated_files.append(new_path)
                    self._emit_file_event("file_renamed", new_path)
                file_idx += 1

            time.sleep(self._get_delay(params))

    def _exec_slow_unique_file_modify(self, params):
        """R6: Slower modification of unique files (stealthy ransomware)."""
        count = self._get_count(params, "file_count", "file_count_range")
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])
        files = self.prepare_test_files(count, extensions)

        for f in files:
            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params))

    def _exec_multi_process_file_modify(self, params):
        """R7: Multiple processes each modifying files."""
        processes = self._get_count(params, "processes", "process_count_range")
        files_per = self._get_count(params, "files_per", "files_per_process_range")
        extensions = params.get("target_extensions", [".txt", ".doc"])
        total_files = processes * files_per
        files = self.prepare_test_files(total_files, extensions)

        file_idx = 0
        for p in range(processes):
            pid = random.randint(1000, 65000)
            proc_name = f"worker_{p}"
            self._emit_process_event("process_started", proc_name, pid)

            for _ in range(files_per):
                if file_idx < len(files):
                    with open(files[file_idx], "wb") as f:
                        f.write(os.urandom(128))
                    self._emit_file_event("file_modified", files[file_idx])
                    file_idx += 1
                time.sleep(self._get_delay(params))

    def _exec_interleaved_network_file(self, params):
        """R8: Network connections interleaved with file modifications."""
        file_count = self._get_count(params, "files", "file_modify_count_range")
        connections = self._get_count(params, "connections", "network_connection_count_range")
        ip_count = self._get_count(params, "ips", "unique_ip_range")
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])

        files = self.prepare_test_files(file_count, extensions)
        ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
               for _ in range(ip_count)]

        # Interleave: emit some network events among file modifications
        net_interval = max(1, file_count // connections) if connections > 0 else file_count + 1
        net_emitted = 0

        for i, f in enumerate(files):
            if i % net_interval == 0 and net_emitted < connections:
                self._emit_network_event(remote_ip=ips[net_emitted % len(ips)])
                net_emitted += 1

            with open(f, "wb") as fp:
                fp.write(os.urandom(128))
            self._emit_file_event("file_modified", f)
            time.sleep(self._get_delay(params))

    def _exec_interleaved_all(self, params):
        """R9: All sources active — file + process + network."""
        file_count = self._get_count(params, "files", "file_modify_count_range")
        processes = self._get_count(params, "processes", "process_event_count_range")
        network = self._get_count(params, "network", "network_event_count_range")
        ip_count = self._get_count(params, "ips", "unique_ip_range") or 2
        extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])

        files = self.prepare_test_files(file_count, extensions)
        ips = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
               for _ in range(ip_count)]

        # Build and shuffle operation queue
        ops = (
            [("file_modify", f) for f in files] +
            [("process", None) for _ in range(processes)] +
            [("network", None) for _ in range(network)]
        )
        random.shuffle(ops)

        for op_type, arg in ops:
            if op_type == "file_modify":
                with open(arg, "wb") as f:
                    f.write(os.urandom(128))
                self._emit_file_event("file_modified", arg)
            elif op_type == "process":
                self._emit_process_event()
            elif op_type == "network":
                self._emit_network_event(remote_ip=ips[random.randint(0, len(ips)-1)])
            time.sleep(self._get_delay(params))

    def _exec_rapid_bulk_rename(self, params):
        """R10: Rapid renaming of many files with suspicious extensions."""
        count = self._get_count(params, "file_count", "file_count_range")
        extension = params.get("extension", ".locked")
        target_extensions = params.get("target_extensions", [".txt", ".doc", ".pdf"])
        files = self.prepare_test_files(count, target_extensions)

        for f in files:
            new_path = f + extension
            os.rename(f, new_path)
            self._generated_files.append(new_path)
            self._emit_file_event("file_renamed", new_path)
            time.sleep(self._get_delay(params))
