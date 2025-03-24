def store_entries_in_file(volume_entries):
    separator = "-" * 40  # creates a line of 40 dashes
    with open("data/volume_entries.txt", "w", encoding="utf-8") as file:
        for entry in volume_entries:
            file.write(entry + "\n")
            file.write(separator + "\n")

    # with open("data/paper_entries.txt", "w", encoding="utf-8") as file:
    #     for entry in paper_entries:
    #         file.write(entry + "\n")
    #         file.write(separator + "\n")