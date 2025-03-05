# utils/bulk_importer.py
from queue import Queue
from threading import Thread
from rdflib import Graph, Namespace
def process_large_data(data, mapper_func, loader_func, batch_size=500):
    q = Queue()
    def worker():
        while True:
            batch = q.get()
            rdf_batch = Graph()
            for item in batch:
                rdf_batch += mapper_func(item)
            loader_func(rdf_batch.serialize())
            q.task_done()
    
    # Start 4 worker threads
    for _ in range(4):
        Thread(target=worker, daemon=True).start()
    
    # Split data into batches
    for i in range(0, len(data), batch_size):
        q.put(data[i:i+batch_size])
    
    q.join()