from evidence_extractor import extract_evidence


context = """
Binary search is an algorithm used to find an element in a sorted array
by repeatedly dividing the search interval in half.

Merge sort is a sorting algorithm that uses the divide-and-conquer technique.
It works by dividing the input array into two halves, recursively sorting them,
and then merging the sorted halves back together.
"""

question = "How is merge sort different from binary search?"

evidence = extract_evidence(question, context)

print("\n========== EXTRACTED EVIDENCE ==========")

for item in evidence:
    print(f"\nConcept: {item['concept']}")
    print(f"Quote: {item['quote']}")