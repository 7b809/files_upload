import os, base64

def save_chunk(filename, chunk_number, chunk_data, upload_dir):
    file_dir = os.path.join(upload_dir, filename + "_parts")
    os.makedirs(file_dir, exist_ok=True)
    part_path = os.path.join(file_dir, f"part_{chunk_number}")
    with open(part_path, "wb") as f:
        f.write(base64.b64decode(chunk_data))


def merge_chunks(filename, total_chunks, upload_dir):
    """Merge when all chunks are received"""
    file_dir = os.path.join(upload_dir, filename + "_parts")
    parts = [os.path.join(file_dir, f"part_{i}") for i in range(total_chunks)]
    if not all(os.path.exists(p) for p in parts):
        return False  # not all parts received

    final_path = os.path.join(upload_dir, filename)
    with open(final_path, "wb") as outfile:
        for p in parts:
            with open(p, "rb") as infile:
                outfile.write(infile.read())

    # cleanup
    for p in parts:
        os.remove(p)
    os.rmdir(file_dir)
    return True
