import re

def clean_transcript(text):

    #remove common transcript labels
    text = re.sub(
        r"\[(music|applause|laughter|inaudiable)\]",
        "",
        text,
        flags=re.IGNORECASE
    )

    #remove html tags
    text = re.sub(r"<[^>]+>","",text)

    #replace multiple space
    text = re.sub(r"\s+"," ",text)

    #remove space before puncuation
    text = re.sub(r"\s+([,.!?:;])",r"\1",text)

    #remove leading\trailing spaces
    text = text.strip()

    return text
