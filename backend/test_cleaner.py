from cleaner import clean_transcript

text = """
[Music]

Hello guys, welcome back!

Today we are going to learn
machine learning.

[Laughter]

Machine learning allows computers
to learn from data.

[Applause]
"""


cleaned_text = clean_transcript(text)

print("----- ORIGINAL -----")
print(text)

print("\n----- CLEANED -----")
print(cleaned_text)