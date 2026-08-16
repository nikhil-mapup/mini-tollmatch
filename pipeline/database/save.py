def save_to_collection(collection, records, batch_size=5000):
    if not records:
        print(f"No records to save to {collection.name}", flush=True)
        return

    deleted = collection.delete_many({})
    print(
        f"Cleared {deleted.deleted_count} existing documents from {collection.name}",
        flush=True,
    )

    total_inserted = 0
    total_records = len(records)

    for start in range(0, total_records, batch_size):
        batch = records[start : start + batch_size]
        documents = [record.model_dump(mode="python") for record in batch]
        result = collection.insert_many(documents)
        total_inserted += len(result.inserted_ids)
        print(
            f"Inserted {total_inserted}/{total_records} documents into {collection.name}",
            flush=True,
        )
