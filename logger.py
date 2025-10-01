# Logging utility for the web crawler

def save_log(filename, log, total_bytes, start_time, error_counts):
    import time

    total_time = round(time.time() - start_time, 2) if start_time else 0
    total_gb = total_bytes / (1000 ** 3)
    total_gib = total_bytes / (1024 ** 3)

    with open(filename, "w") as f:
        for e in log:
            f.write(
                f"{e['url']} | {e['time']} | size={e['size']} | depth={e['depth']} | "
                f"code={e['return_code']} | priority={e['priority']} | elapsed={e['elapsed']}s\n"
            )
        f.write("\n--- Summary Statistics ---\n")
        f.write(f"Total pages crawled: {len(log)}\n")
        f.write(f"Total size (bytes): {total_bytes}\n")
        f.write(f"Total size (GB): {total_gb:.3f}\n")
        f.write(f"Total size (GiB): {total_gib:.3f}\n")
        f.write(f"Total time (s): {total_time}\n")
        rate = round(len(log) / total_time, 2) if total_time > 0 else "N/A"
        f.write(f"Pages/sec: {rate}\n")
        for code, count in error_counts.items():
            f.write(f"Errors {code}: {count}\n")
