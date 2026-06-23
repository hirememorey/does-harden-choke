"""Foul-Type Video Grader using Multimodal LLMs.

Grades the TIMING axis (BEFORE, DURING, AFTER) of shooting fouls from video clips.
Supports Google (Gemini — recommended, native video), OpenAI (GPT-5.4 mini), and Anthropic (Claude Sonnet 4.6).

Recommended usage (Gemini — native video understanding, no frame extraction):
    python src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash"

Validate against manual ground truth first:
    python src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash" --validate-only

Alternative providers (frame-based, less temporal precision):
    python src/foul_type_llm_grader.py --player "James Harden" --provider "openai" --model "gpt-5.4-mini"
    python src/foul_type_llm_grader.py --player "James Harden" --provider "anthropic" --model "claude-sonnet-4-6"
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert NBA officiating analyst. Your task is to watch a short video clip (or a chronological sequence of frames) of a shooting foul and determine WHEN the first illegal contact occurs relative to the shooter's upward shooting motion.

Focus ONLY on timing — when the contact happens relative to the shot release. Do not judge whether the call was correct, how hard the contact was, or what type of foul it was.

BEFORE: Contact occurs while the shooter's arms are still LOW — gathering the ball, dribbling, bringing the ball up, or in a rip-through motion. The upward shooting motion has NOT started yet. The shooter's arms have not begun rising toward the release point.

DURING: Contact occurs while the shooter's arms are RISING in the shooting motion. The ball has not yet left the shooter's hands. The shooter is in the act of shooting — arms moving upward toward the release.

AFTER: Contact occurs AFTER the ball has left the shooter's hands. The ball is already in the air. Contact happens on the follow-through, landing, or after release.

UNKNOWN: The camera angle makes it impossible to see when contact occurred, or no clear contact is visible.

Return a JSON object:
{
  "timing": "BEFORE" | "DURING" | "AFTER" | "UNKNOWN",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "One sentence: where were the shooter's arms when contact occurred?"
}"""


# ---------------------------------------------------------------------------
# Frame Extraction Helper using local ffmpeg
# ---------------------------------------------------------------------------

def extract_frames_with_ffmpeg(video_path: str, output_dir: str, fps: float = 1.0) -> List[str]:
    """Extract frames from video at specific fps using local ffmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    # Target naming: frame_0001.jpg, frame_0002.jpg
    frame_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    
    # We find ffmpeg path on mac
    ffmpeg_path = "/opt/local/bin/ffmpeg" if os.path.exists("/opt/local/bin/ffmpeg") else "ffmpeg"
    
    cmd = [
        ffmpeg_path, "-y", "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",  # high quality JPEGs
        frame_pattern
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # List and sort the generated frames
    frames = sorted([
        os.path.join(output_dir, f) for f in os.listdir(output_dir)
        if f.startswith("frame_") and f.endswith(".jpg")
    ])
    return frames


def encode_image_base64(image_path: str) -> str:
    """Encode binary image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# Grader Base and Provider Subclasses (Pure requests-based to avoid library dependencies)
# ---------------------------------------------------------------------------

class LLMGrader(ABC):
    """Abstract Base Class for LLM-based video grading."""

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    def grade_clip(self, video_path: str, description: str) -> Dict[str, Any]:
        """Grade a single video clip given its path and PBP play description."""
        pass

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Utility to safely extract and parse JSON object from LLM response text."""
        # Find JSON boundaries
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Failed to parse model response: {text[:200]}"}


class OpenAIGrader(LLMGrader):
    """Grader using OpenAI's chat completions API (GPT-5.4-mini / GPT-5.4)."""

    def grade_clip(self, video_path: str, description: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract at 3fps to capture the ~0.2s gather-to-release transition; cap at 15 frames
            frames = extract_frames_with_ffmpeg(video_path, temp_dir, fps=3.0)
            if not frames:
                return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": "Could not extract frames from video."}
            frames = frames[:15]
            
            # OpenAI prompt structure
            content: List[Dict[str, Any]] = [
                {"type": "text", "text": f"Play-by-play description: {description}\n\nAnalyze the chronological sequence of frames below and determine the timing of the foul contact."}
            ]
            
            # Append images
            for f in frames:
                b64 = encode_image_base64(f)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "low"  # low detail saves tokens and cost
                    }
                })

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0
            }

            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"OpenAI API Error {resp.status_code}: {resp.text}"}
            
            res_text = resp.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(res_text)


class AnthropicGrader(LLMGrader):
    """Grader using Anthropic's Messages API (Claude Sonnet 4.6 / Claude Haiku 4.5)."""

    def grade_clip(self, video_path: str, description: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 2fps to capture the gather-to-release transition; cap at 10 frames for Claude token limits
            frames = extract_frames_with_ffmpeg(video_path, temp_dir, fps=2.0)
            if not frames:
                return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": "Could not extract frames from video."}
            
            frames = frames[:10]  # cap at 10 frames to avoid rate limits / context limits
            
            content: List[Dict[str, Any]] = []
            # Append frames first
            for f in frames:
                b64 = encode_image_base64(f)
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64
                    }
                })
            
            # Append prompt text at the end
            prompt = f"Play-by-play description: {description}\n\nAnalyze the chronological sequence of frames above. Determine the contact timing relative to the shot release."
            content.append({
                "type": "text",
                "text": prompt
            })

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "max_tokens": 400,
                "system": SYSTEM_PROMPT + "\nReturn ONLY raw JSON, do not wrap in markdown code blocks.",
                "messages": [
                    {"role": "user", "content": content}
                ],
                "temperature": 0.0
            }

            resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            if resp.status_code != 200:
                return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Anthropic API Error {resp.status_code}: {resp.text}"}
            
            res_text = resp.json()["content"][0]["text"]
            return self._parse_json_response(res_text)


class VertexGeminiGrader(LLMGrader):
    """Grader using Vertex AI Gemini via gcloud ADC — no API key required.

    Authenticates via ``gcloud auth application-default print-access-token``,
    uploads videos to a GCS bucket, and calls the Vertex AI generateContent
    endpoint with native video understanding.
    """

    GCS_BUCKET = "project-3984c931-3755-423f-966-foul-type-grader-tmp"
    LOCATION = "us-central1"

    def __init__(self, model_name: str, project: Optional[str] = None):
        super().__init__(api_key="", model_name=model_name)
        self.project = project or self._detect_project()
        self._token_cache: Tuple[float, str] = (0.0, "")

    @staticmethod
    def _detect_project() -> str:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True,
        )
        project = result.stdout.strip()
        if not project:
            raise RuntimeError("Could not detect GCP project. Run `gcloud config set project <PROJECT>`.")
        return project

    def _access_token(self) -> str:
        ts, tok = self._token_cache
        if tok and (time.time() - ts) < 300:
            return tok
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True,
        )
        token = result.stdout.strip()
        if not token:
            raise RuntimeError("Failed to obtain access token via gcloud ADC.")
        self._token_cache = (time.time(), token)
        return token

    def _upload_to_gcs(self, local_path: str, object_name: str) -> str:
        token = self._access_token()
        url = f"https://storage.googleapis.com/upload/storage/v1/b/{self.GCS_BUCKET}/o"
        params = {"uploadType": "media", "name": object_name}
        with open(local_path, "rb") as f:
            data = f.read()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "video/mp4",
        }
        resp = requests.post(url, headers=headers, params=params, data=data)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"GCS upload failed ({resp.status_code}): {resp.text}")
        return f"gs://{self.GCS_BUCKET}/{object_name}"

    def _delete_gcs_object(self, object_name: str) -> None:
        token = self._access_token()
        url = f"https://storage.googleapis.com/storage/v1/b/{self.GCS_BUCKET}/o/{object_name}"
        headers = {"Authorization": f"Bearer {token}"}
        requests.delete(url, headers=headers)

    def grade_clip(self, video_path: str, description: str) -> Dict[str, Any]:
        token = self._access_token()
        object_name = f"grader_tmp/{os.path.basename(video_path)}"

        try:
            gcs_uri = self._upload_to_gcs(video_path, object_name)
        except Exception as exc:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"GCS upload error: {exc}"}

        generate_url = (
            f"https://{self.LOCATION}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project}/locations/{self.LOCATION}/"
            f"publishers/google/models/{self.model_name}:generateContent"
        )
        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"file_data": {"mime_type": "video/mp4", "file_uri": gcs_uri}},
                    {"text": SYSTEM_PROMPT + f"\n\nPlay-by-play description: {description}\nAnalyze this video and return a raw JSON object."}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(generate_url, headers=headers, json=payload)
            if resp.status_code != 200:
                return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Vertex AI Error {resp.status_code}: {resp.text[:500]}"}
            res_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(res_text)
        except Exception as exc:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Vertex AI parse error: {exc}"}
        finally:
            try:
                self._delete_gcs_object(object_name)
            except Exception:
                logger.warning("Failed to delete GCS object %s", object_name)


class GeminiGrader(LLMGrader):
    """Grader using Google's Gemini API via direct File uploads (best native video understanding)."""

    def grade_clip(self, video_path: str, description: str) -> Dict[str, Any]:
        # Step 1: Upload video using the Google Files API
        file_size = os.path.getsize(video_path)
        
        # Initiate resumable upload session
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": "video/mp4",
            "Content-Type": "application/json",
        }
        
        metadata = {
            "file": {"display_name": os.path.basename(video_path)}
        }
        
        url_upload_init = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={self.api_key}"
        resp_init = requests.post(url_upload_init, headers=headers, json=metadata)
        if resp_init.status_code != 200:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Gemini Upload Init Error: {resp_init.text}"}
        
        upload_url = resp_init.headers.get("X-Goog-Upload-URL")
        if not upload_url:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": "Gemini Upload URL not returned."}
        
        # Upload actual bytes
        headers_upload = {
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
            "Content-Length": str(file_size),
        }
        with open(video_path, "rb") as f:
            resp_upload = requests.post(upload_url, headers=headers_upload, data=f.read())
            
        if resp_upload.status_code != 200:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Gemini Upload Bytes Error: {resp_upload.text}"}
            
        file_info = resp_upload.json()
        file_uri = file_info.get("file", {}).get("uri")
        file_name = file_info.get("file", {}).get("name")
        
        if not file_uri:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": "Gemini File URI not returned."}

        # Step 2: Poll file processing status until ACTIVE
        headers_get = {"Content-Type": "application/json"}
        get_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={self.api_key}"
        
        status = "PROCESSING"
        max_attempts = 15
        attempt = 0
        while status == "PROCESSING" and attempt < max_attempts:
            time.sleep(2)
            resp_get = requests.get(get_url, headers=headers_get)
            if resp_get.status_code == 200:
                status = resp_get.json().get("state", "PROCESSING")
            attempt += 1
            
        if status != "ACTIVE":
            # Clean up file and exit
            requests.delete(get_url)
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Gemini Video Processing failed/timeout (state={status})"}

        # Step 3: Run generateContent call
        generate_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}},
                    {"text": SYSTEM_PROMPT + f"\n\nPlay-by-play description: {description}\nAnalyze this video and return a raw JSON object."}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        }
        
        resp_gen = requests.post(generate_url, headers=headers_get, json=payload)
        
        # Clean up file on Google servers immediately
        requests.delete(get_url)
        
        if resp_gen.status_code != 200:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Gemini Generation Error: {resp_gen.text}"}
            
        try:
            res_text = resp_gen.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(res_text)
        except Exception as e:
            return {"timing": "UNKNOWN", "confidence": "LOW", "reasoning": f"Failed parsing Gemini candidate: {e}"}


# ---------------------------------------------------------------------------
# Data and Ground Truth Loading Helper
# ---------------------------------------------------------------------------

def load_ground_truth() -> Dict[Tuple[str, int], str]:
    """Load manual timing classifications from foul_type_classifications.csv."""
    gt_path = config.PROJECT_ROOT / "foul_type_classifications.csv"
    if not gt_path.exists():
        return {}
    
    df = pd.read_csv(gt_path, low_memory=False)
    df = df.dropna(subset=["timing"])
    
    # Map (game_id, event_id) -> timing
    # Pad game_id with leading zeros if it's numeric
    gt = {}
    for _, row in df.iterrows():
        gid = str(row["game_id"]).zfill(10)
        eid = int(row["event_id"])
        gt[(gid, eid)] = row["timing"].strip()
    return gt


def load_manifest(player: str, season_type: str = "Regular Season") -> Dict[str, Any]:
    """Load player manifest json. Checks for PO-specific manifest when season_type is Playoffs."""
    slug = config.player_slug(player)
    suffix = "_po" if season_type == "Playoffs" else ""
    manifest_path = config.PROCESSED_DIR / f"foul_type_manifest_{slug}{suffix}.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}\nRun the appropriate foul-type-scrape target first.")
    with open(manifest_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Main Execution Loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Multimodal LLM video foul timing grader")
    parser.add_argument("--player", required=True, help="Player name (must match config.py)")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "gemini", "vertex"], help="LLM Provider")
    parser.add_argument("--model", required=True, help="Model name (e.g. gpt-5.4-mini, claude-sonnet-4-6, gemini-2.5-flash)")
    parser.add_argument("--season-type", default="Regular Season", help="Regular Season or Playoffs (selects the correct manifest)")
    parser.add_argument("--limit", type=int, default=None, help="Limit grading to first N clips")
    parser.add_argument("--validate-only", action="store_true", help="Only grade clips that have manual ground truth in foul_type_classifications.csv")
    args = parser.parse_args()

    # Get API key from env (vertex uses gcloud ADC — no key needed)
    key_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY"
    }

    if args.provider == "vertex":
        api_key = ""
    else:
        env_var = key_env_map[args.provider]
        api_key = os.getenv(env_var) or (os.getenv("GOOGLE_API_KEY") if args.provider == "gemini" else None)

        if not api_key:
            print(f"Error: API key for {args.provider} not found in environment ({env_var}).")
            sys.exit(1)

    # Initialize Grader
    if args.provider == "openai":
        grader = OpenAIGrader(api_key, args.model)
    elif args.provider == "anthropic":
        grader = AnthropicGrader(api_key, args.model)
    elif args.provider == "vertex":
        grader = VertexGeminiGrader(args.model)
    else:
        grader = GeminiGrader(api_key, args.model)

    # Load data
    manifest = load_manifest(args.player, args.season_type)
    ground_truth = load_ground_truth()
    
    clips = manifest.get("clips", [])

    if args.validate_only:
        clips = [c for c in clips if (str(c['game_id']).zfill(10), int(c['event_id'])) in ground_truth]
        if not clips:
            print("ERROR: --validate-only specified but no clips match ground truth in foul_type_classifications.csv")
            sys.exit(1)

    if args.limit:
        clips = clips[:args.limit]

    gt_count = sum(1 for c in clips if (str(c['game_id']).zfill(10), int(c['event_id'])) in ground_truth)

    print(f"\n" + "="*70)
    print(f"LLM VIDEO GRADER RUN: {args.player}")
    print(f"Provider:  {args.provider.upper()} ({args.model})")
    print(f"Clips:     {len(clips)}{' (validate-only)' if args.validate_only else ' from manifest'}")
    print(f"Ground Truth matches: {gt_count} / {len(clips)}")
    print("="*70 + "\n")

    results = []
    temp_video_dir = tempfile.mkdtemp()
    
    # Store validation analytics
    val_comparisons = []

    try:
        for idx, c in enumerate(tqdm(clips, desc="Grading clips")):
            game_id = str(c["game_id"]).zfill(10)
            event_id = int(c["event_id"])
            video_url = c["video_url_960"]
            description = c["description"]
            
            # Download video locally
            local_video_path = os.path.join(temp_video_dir, f"clip_{game_id}_{event_id}.mp4")
            try:
                resp = requests.get(video_url, timeout=15)
                if resp.status_code == 200:
                    with open(local_video_path, "wb") as f:
                        f.write(resp.content)
                else:
                    logger.warning("Failed downloading video %s: HTTP %d", video_url, resp.status_code)
                    continue
            except Exception as e:
                logger.warning("Error downloading video %s: %s", video_url, e)
                continue
            
            # Run grading
            grade = grader.grade_clip(local_video_path, description)
            
            # Record result
            res_entry = {
                "game_id": game_id,
                "event_id": event_id,
                "description": description,
                "predicted_timing": grade.get("timing", "UNKNOWN"),
                "confidence": grade.get("confidence", "LOW"),
                "reasoning": grade.get("reasoning", ""),
                "opponent": c["opponent"]
            }
            
            # Cross-reference with Ground Truth
            gt_key = (game_id, event_id)
            if gt_key in ground_truth:
                gt_timing = ground_truth[gt_key]
                res_entry["ground_truth_timing"] = gt_timing
                val_comparisons.append({
                    "game_id": game_id,
                    "event_id": event_id,
                    "gt": gt_timing,
                    "pred": grade.get("timing", "UNKNOWN"),
                    "reasoning": grade.get("reasoning", ""),
                    "desc": description
                })
            
            results.append(res_entry)
            
    finally:
        shutil.rmtree(temp_video_dir, ignore_errors=True)

    # Save results
    slug = config.player_slug(args.player)
    out_path = config.PROCESSED_DIR / f"foul_type_llm_results_{slug}.json"
    
    output_payload = {
        "player": args.player,
        "provider": args.provider,
        "model": args.model,
        "timestamp": pd.Timestamp.now().isoformat(),
        "num_graded": len(results),
        "results": results
    }
    with open(out_path, "w") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\n" + "="*70)
    print(f"RUN COMPLETE. Results saved to {out_path}")
    print("="*70 + "\n")

    # Display Validation Analytics
    if val_comparisons:
        vdf = pd.DataFrame(val_comparisons)
        # Compute accuracy (ignoring UNKNOWNs in ground truth or predictions if needed, but here absolute matches)
        correct = (vdf["gt"] == vdf["pred"]).sum()
        accuracy = correct / len(vdf)
        
        print("*"*70)
        print("VALIDATION ANALYSIS vs MANUAL GROUND TRUTH (accuracy check)")
        print("*"*70)
        print(f"Matched comparisons: {len(vdf)}")
        print(f"Exact timing matches: {correct}")
        print(f"Accuracy Rate:        {accuracy:.1%}\n")
        
        # Display breakdown
        print("Accuracy Breakdown by Ground Truth Class:")
        for gt_class in ["BEFORE", "DURING", "AFTER"]:
            subset = vdf[vdf["gt"] == gt_class]
            if len(subset) > 0:
                sub_correct = (subset["gt"] == subset["pred"]).sum()
                sub_acc = sub_correct / len(subset)
                print(f"  {gt_class:8s} : {sub_correct}/{len(subset)} correct ({sub_acc:.1%})")
                
        print("\nConfusion Matrix:")
        ct = pd.crosstab(vdf["gt"], vdf["pred"], margins=True)
        print(ct.to_string())
        
        print("\nMismatched Cases Detail:")
        mismatch = vdf[vdf["gt"] != vdf["pred"]]
        for _, row in mismatch.iterrows():
            print(f"  Clip {row['game_id']}_{row['event_id']}:")
            print(f"    PBP:     {row['desc'][:70]}...")
            print(f"    GT:      {row['gt']}")
            print(f"    Pred:    {row['pred']}")
            print(f"    Reason:  {row['reasoning']}")
            print()
            
    else:
        print("No ground truth comparisons were available in this run to validate predictions.")


if __name__ == "__main__":
    main()
