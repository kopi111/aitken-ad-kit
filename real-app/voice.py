# This script asks the Ava voice to read each scene and keeps the timing of every word.
import asyncio, json, edge_tts
VOICE = "en-US-AvaMultilingualNeural"
SCENES = [
 "Who's really signing up with your business? Here's our KYC system, running for real.",
 "Their record comes up, and they photograph their ID card.",
 "Then a quick selfie, with a liveness check.",
 "It compares the face with the card, reads the details, and checks them against your records. Right person? Confirmed.",
 "Now, someone else tries to use Keisha's card.",
 "Different face. Not confirmed.",
 "And your team sees every check: both photos, the card details, and the system's verdict. Then they make the final call.",
 "It's made for lenders, credit unions, car rentals, money transfer, landlords, and online stores. Your logo, your records, your own server.",
 "And until December fifteenth, it's thirty percent off. Comment KYC, and we'll send you the details.",
]
# This function saves one scene's audio and returns its word timings in seconds.
async def speak(i, text):
    talk = edge_tts.Communicate(text, VOICE, rate="+3%", boundary="WordBoundary")
    words = []
    with open(f"s{i}.mp3", "wb") as f:
        async for chunk in talk.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append([chunk["offset"] / 1e7, (chunk["offset"] + chunk["duration"]) / 1e7, chunk["text"]])
    return words
async def main():
    out = [await speak(i, t) for i, t in enumerate(SCENES)]
    for scene, w in zip(SCENES, out):
        tokens = scene.split()
        if len(tokens) == len(w):
            for item, token in zip(w, tokens): item[2] = token
    json.dump(out, open("words.json", "w"))
asyncio.run(main())
