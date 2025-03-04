import threading
import queue
import time
import csv


class CSVLogger:
    """Logs rows to a CSV file in a background thread with persistent file handle and batching."""

    def __init__(self, filename, fieldnames, flush_interval=1.0, batch_size=10):
        """
        Args:
            filename (str): Name of the CSV file.
            fieldnames (list): List of CSV column names.
            flush_interval (float): Time (in seconds) between forced flushes.
            batch_size (int): Number of rows to accumulate before writing.
        """
        self.filename = filename
        self.fieldnames = fieldnames
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.row_queue = queue.Queue()
        self.stop_event = threading.Event()

        # Open file once and create a writer.
        self.outfile = open(self.filename, "a", newline="")
        self.writer = csv.DictWriter(self.outfile, fieldnames=self.fieldnames)

        # Write header if the file is new (i.e. if it's empty)
        if self.outfile.tell() == 0:
            self.writer.writeheader()
            self.outfile.flush()

        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def log(self, row):
        """Push a new row (dictionary) into the logging queue."""
        self.row_queue.put(row)

    def _worker(self):
        """Worker thread: accumulate rows and write them in batch."""
        last_flush = time.time()
        batch = []
        while not self.stop_event.is_set():
            try:
                # Wait up to flush_interval for a row.
                row = self.row_queue.get(timeout=self.flush_interval)
                batch.append(row)
            except queue.Empty:
                # Timeout reached, proceed to check if we need to flush.
                pass

            now = time.time()
            # Write batch if batch size reached or flush interval elapsed.
            if batch and (
                len(batch) >= self.batch_size
                or (now - last_flush) >= self.flush_interval
            ):
                for r in batch:
                    self.writer.writerow(r)
                self.outfile.flush()
                batch = []
                last_flush = now

        # Flush any remaining rows after stop signal.
        while not self.row_queue.empty():
            batch.append(self.row_queue.get())
        if batch:
            for r in batch:
                self.writer.writerow(r)
            self.outfile.flush()

    def stop(self):
        """Signal the logger to stop and close the file after the thread finishes."""
        self.stop_event.set()
        self.thread.join()
        self.outfile.close()
