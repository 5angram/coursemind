from process_video import process_video
from embedding import create_embedding

video_id = "VTLCoHnyACE"

result = process_video(video_id ,"Flowchart & Pseudocode")

if result:
    chunks = result["chunks"]
    embeddings = create_embedding(chunks)
    print("\n========== TEST COMPLETE ==========")
    print("Chunks:", len(chunks))
    print("Embeddings:", embeddings.shape)