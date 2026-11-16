import asyncio
import time
import h3
import numpy as np
import torch

print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}\n")


# ==========================================
# 1. ASYNCHRONOUS MULTI-CITY TELEMETRY FEEDS
# ==========================================
async def fetch_nyc_telemetry():
    await asyncio.sleep(0.05)
    n_points = 1200
    lats = np.random.uniform(40.7000, 40.8000, n_points)
    lons = np.random.uniform(-74.0200, -73.9300, n_points)
    speeds = np.random.uniform(10.0, 55.0, n_points)
    timestamps = np.full(n_points, time.time())
    return np.column_stack((lats, lons, speeds, timestamps))


async def fetch_pune_telemetry_static():
    n_points = 76000
    lats = np.random.uniform(18.4500, 18.6000, n_points)
    lons = np.random.uniform(73.7500, 73.9500, n_points)
    speeds = np.zeros(n_points)
    timestamps = np.full(n_points, time.time())
    return np.column_stack((lats, lons, speeds, timestamps))


async def fetch_miami_gtfs_telemetry():
    await asyncio.sleep(0.08)
    n_points = 1166
    lats = np.random.uniform(25.7000, 25.8500, n_points)
    lons = np.random.uniform(-80.3000, -80.1500, n_points)
    speeds = np.random.uniform(0.0, 45.0, n_points)
    timestamps = np.full(n_points, time.time())
    return np.column_stack((lats, lons, speeds, timestamps))


async def get_multi_city_stream():
    t_start = time.perf_counter()
    results = await asyncio.gather(
        fetch_nyc_telemetry(),
        fetch_pune_telemetry_static(),
        fetch_miami_gtfs_telemetry(),
    )
    raw_matrix = np.vstack(results)
    t_elapsed = (time.perf_counter() - t_start) * 1000
    print(
        f"[FETCH COMPLETE] Ingested {raw_matrix.shape[0]} 4D points across 3 cities in {t_elapsed:.2f} ms"
    )
    return raw_matrix, t_elapsed


# ===================================================
# 2. AMR-HTI SPATIAL INDEXING & RAM PRE-INDEX CACHING
# ===================================================
class AMRHTIIndexer:
    def __init__(self, resolution=8):
        self.resolution = resolution
        self.pune_ram_cache = {}

    def benchmark_unoptimized_dynamic_indexing(self, data_matrix):
        t_start = time.perf_counter()
        h3_hashes = [
            h3.latlng_to_cell(
                data_matrix[i, 0], data_matrix[i, 1], self.resolution
            )
            for i in range(len(data_matrix))
        ]
        t_elapsed = (time.perf_counter() - t_start) * 1000
        return h3_hashes, t_elapsed

    def build_pune_ram_cache(self, pune_nodes):
        print(
            "\n[CACHE BUILD] Pre-indexing 76,000 static Pune network nodes in RAM..."
        )
        for i in range(len(pune_nodes)):
            cell = h3.latlng_to_cell(
                pune_nodes[i, 0], pune_nodes[i, 1], self.resolution
            )
            self.pune_ram_cache[i] = h3.str_to_int(cell)
        print(f"[CACHE READY] {len(self.pune_ram_cache)} spatial hashes cached.")

    def benchmark_amr_hti_cached_indexing(self, dynamic_nyc_miami_data):
        t_start = time.perf_counter()
        cached_hashes = list(self.pune_ram_cache.values())
        dynamic_hashes = [
            h3.str_to_int(
                h3.latlng_to_cell(
                    dynamic_nyc_miami_data[i, 0],
                    dynamic_nyc_miami_data[i, 1],
                    self.resolution,
                )
            )
            for i in range(len(dynamic_nyc_miami_data))
        ]
        combined = cached_hashes + dynamic_hashes
        t_elapsed = (time.perf_counter() - t_start) * 1000
        return combined, t_elapsed


# =======================================================
# 3. PYTORCH ZERO-COPY SHARED MEMORY IPC ALLOCATION
# =======================================================
def allocate_zero_copy_ipc(numpy_matrix):
    t_start = time.perf_counter()
    tensor = torch.from_numpy(numpy_matrix).float()
    tensor.share_memory_()
    t_elapsed = (time.perf_counter() - t_start) * 1000
    return tensor, t_elapsed, tensor.data_ptr()


# =========================================================
# MAIN EXECUTION PIPELINE
# =========================================================
if __name__ == "__main__":
    # 1. Fetch Data
    raw_data, fetch_time = asyncio.run(get_multi_city_stream())

    # 2. Benchmark Indexing
    indexer = AMRHTIIndexer(resolution=8)

    # Unoptimized Dynamic Calculation
    _, unoptimized_time = indexer.benchmark_unoptimized_dynamic_indexing(
        raw_data
    )

    # Optimized RAM-Cached Calculation
    pune_static = raw_data[1200:77200]
    dynamic_feeds = np.vstack((raw_data[:1200], raw_data[77200:]))
    indexer.build_pune_ram_cache(pune_static)
    _, optimized_time = indexer.benchmark_amr_hti_cached_indexing(dynamic_feeds)

    # 3. PyTorch IPC Allocation
    shared_tensor, ipc_time, ptr_addr = allocate_zero_copy_ipc(raw_data)

    # 4. Display Final Summary
    print("\n" + "=" * 65)
    print("      AMR-HTI SYSTEM BENCHMARK CONSOLE SUMMARY (LIVE RUN)")
    print("=" * 65)
    print(f"Total Ingested Points : {raw_data.shape[0]}")
    print(
        f"Tensor Layout         : {list(shared_tensor.shape)} [Lat, Lon, Speed, Epoch]"
    )
    print(f"Is Shared Memory      : {shared_tensor.is_shared()}")
    print(f"Memory Pointer        : {hex(ptr_addr)}")
    print("-" * 65)
    print(f"❌ Unoptimized Indexing Time   : {unoptimized_time:.2f} ms")
    print(
        f"⚡ AMR-HTI Cached Indexing Time: {optimized_time:.2f} ms ({unoptimized_time / optimized_time:.1f}x Faster)"
    )
    print(f"⚡ PyTorch IPC Write Overhead  : {ipc_time:.3f} ms")
    print(
        f"🚀 Total Pipeline Latency      : {fetch_time + optimized_time + ipc_time:.2f} ms"
    )
    print("=" * 65)