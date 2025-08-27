import hashlib
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from axiestudio.custom import Component
from axiestudio.inputs import BoolInput, DropdownInput, HandleInput, IntInput
from axiestudio.schema import Data
from axiestudio.template import Output


class SplitVideoComponent(Component):
    """En komponent som delar upp en video i flera klipp med en viss varaktighet med hjälp av FFmpeg."""

    display_name = "Dela video"
    description = "Dela en video i flera klipp med specificerad längd."
    icon = "TwelveLabs"
    name = "SplitVideo"
    documentation = "https://github.com/twelvelabs-io/twelvelabs-developer-experience/blob/main/integrations/Langflow/TWELVE_LABS_COMPONENTS_README.md"

    inputs = [
        HandleInput(
            name="videodata",
            display_name="Videodata",
            info="Indata videodata från VideoFile-komponenten",
            required=True,
            input_types=["Data"],
        ),
        IntInput(
            name="clip_duration",
            display_name="Klipplängd (sekunder)",
            info="Längden på varje klipp i sekunder",
            required=True,
            value=30,
        ),
        DropdownInput(
            name="last_clip_handling",
            display_name="Hantering av sista klipp",
            info=(
                "Hur det sista klippet ska hanteras när det skulle bli kortare än den specificerade längden:\n"
                "- Trunkera: Hoppa över det sista klippet helt om det är kortare än den specificerade längden\n"
                "- Överlappa föregående: Starta det sista klippet tidigare för att behålla full längd, "
                "överlappande med föregående klipp\n"
                "- Behåll kort: Behåll det sista klippet i sin naturliga längd, även om det är kortare än specificerad längd"
            ),
            options=["Truncate", "Overlap Previous", "Keep Short"],
            value="Overlap Previous",
            required=True,
        ),
        BoolInput(
            name="include_original",
            display_name="Inkludera originalvideon",
            info="Om du vill inkludera originalvideon i utdata",
            value=False,
        ),
    ]

    outputs = [
        Output(
            name="clips",
            display_name="Videoklipp",
            method="process",
            output_types=["Data"],
        ),
    ]

    def get_video_duration(self, video_path: str) -> float:
        """Hämta videolängd med hjälp av FFmpeg."""
        try:
            # Validera videoplatsen för att förhindra skrivning till shell
            if not isinstance(video_path, str) or any(c in video_path for c in ";&|`$(){}[]<>*?!#~"):
                error_msg = "Ogiltig videoplats"
                raise ValueError(error_msg)

            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,  # Explicitly set shell=False for security (S603)
            )
            if result.returncode != 0:
                error_msg = f"FFprobe error: {result.stderr}"
                raise RuntimeError(error_msg)
            return float(result.stdout.strip())
        except Exception as e:
            self.log(f"Error getting video duration: {e!s}", "ERROR")
            raise

    def get_output_dir(self, video_path: str) -> str:
        """Skapa en unik utdatakatalog för klipp baserat på videonamn och tidsstämpel."""
        # Hämta videofilnamnet utan filändelse
        path_obj = Path(video_path)
        base_name = path_obj.stem

        # Skapa en tidsstämpel
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

        # Create a unique hash from the video path
        path_hash = hashlib.sha256(video_path.encode()).hexdigest()[:8]

        # Create the output directory path
        output_dir = Path(path_obj.parent) / f"clips_{base_name}_{timestamp}_{path_hash}"

        # Create the directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        return str(output_dir)

    def process_video(self, video_path: str, clip_duration: int, *, include_original: bool) -> list[Data]:
        """Behandla videon och dela upp den i klipp med hjälp av FFmpeg."""
        try:
            # Hämta videolängd
            total_duration = self.get_video_duration(video_path)

            # Calculate number of clips (ceiling to include partial clip)
            num_clips = math.ceil(total_duration / clip_duration)
            self.log(
                f"Total duration: {total_duration}s, Clip duration: {clip_duration}s, Number of clips: {num_clips}"
            )

            # Create output directory for clips
            output_dir = self.get_output_dir(video_path)

            # Get original video info
            path_obj = Path(video_path)
            original_filename = path_obj.name
            original_name = path_obj.stem

            # List to store all video paths (including original if requested)
            video_paths: list[Data] = []

            # Add original video if requested
            if include_original:
                original_data: dict[str, Any] = {
                    "text": video_path,
                    "metadata": {
                        "source": video_path,
                        "type": "video",
                        "clip_index": -1,  # -1 indicates original video
                        "duration": int(total_duration),  # Convert to int
                        "original_video": {
                            "name": original_name,
                            "filename": original_filename,
                            "path": video_path,
                            "duration": int(total_duration),  # Convert to int
                            "total_clips": int(num_clips),
                            "clip_duration": int(clip_duration),
                        },
                    },
                }
                video_paths.append(Data(data=original_data))

            # Split video into clips
            for i in range(int(num_clips)):  # Convert num_clips to int for range
                start_time = float(i * clip_duration)  # Convert to float for time calculations
                end_time = min(float((i + 1) * clip_duration), total_duration)
                duration = end_time - start_time

                # Handle last clip if it's shorter
                if i == int(num_clips) - 1 and duration < clip_duration:  # Convert num_clips to int for comparison
                    if self.last_clip_handling == "Truncate":
                        # Skip if the last clip would be too short
                        continue
                    if self.last_clip_handling == "Overlap Previous" and i > 0:
                        # Start from earlier to make full duration
                        start_time = total_duration - clip_duration
                        duration = clip_duration
                    # For "Keep Short", we use the original start_time and duration

                # Skip if duration is too small (less than 1 second)
                if duration < 1:
                    continue

                # Generate output path
                output_path = Path(output_dir) / f"clip_{i:03d}.mp4"
                output_path_str = str(output_path)

                try:
                    # Use FFmpeg to split the video
                    cmd = [
                        "ffmpeg",
                        "-i",
                        video_path,
                        "-ss",
                        str(start_time),
                        "-t",
                        str(duration),
                        "-c:v",
                        "libx264",
                        "-c:a",
                        "aac",
                        "-y",  # Overwrite output file if it exists
                        output_path_str,
                    ]

                    result = subprocess.run(  # noqa: S603
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        shell=False,  # Explicitly set shell=False for security
                    )
                    if result.returncode != 0:
                        error_msg = f"FFmpeg error: {result.stderr}"
                        raise RuntimeError(error_msg)

                    # Create timestamp string for metadata
                    start_min = int(start_time // 60)
                    start_sec = int(start_time % 60)
                    end_min = int(end_time // 60)
                    end_sec = int(end_time % 60)
                    timestamp_str = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

                    # Create Data object for the clip
                    clip_data: dict[str, Any] = {
                        "text": output_path_str,
                        "metadata": {
                            "source": video_path,
                            "type": "video",
                            "clip_index": i,
                            "start_time": float(start_time),
                            "end_time": float(end_time),
                            "duration": float(duration),
                            "original_video": {
                                "name": original_name,
                                "filename": original_filename,
                                "path": video_path,
                                "duration": int(total_duration),
                                "total_clips": int(num_clips),
                                "clip_duration": int(clip_duration),
                            },
                            "clip": {
                                "index": i,
                                "total": int(num_clips),
                                "duration": float(duration),
                                "start_time": float(start_time),
                                "end_time": float(end_time),
                                "timestamp": timestamp_str,
                            },
                        },
                    }
                    video_paths.append(Data(data=clip_data))

                except Exception as e:
                    self.log(f"Error processing clip {i}: {e!s}", "ERROR")
                    raise

            self.log(f"Created {len(video_paths)} clips in {output_dir}")
        except Exception as e:
            self.log(f"Error processing video: {e!s}", "ERROR")
            raise
        else:
            return video_paths

    def process(self) -> list[Data]:
        """Process the input video and return a list of Data objects containing the clips."""
        try:
            # Get the input video path from the previous component
            if not hasattr(self, "videodata") or not isinstance(self.videodata, list) or len(self.videodata) != 1:
                error_msg = "Please provide exactly one video"
                raise ValueError(error_msg)

            video_path = self.videodata[0].data.get("text")
            if not video_path or not Path(video_path).exists():
                error_msg = "Invalid video path"
                raise ValueError(error_msg)

            # Validate video path to prevent shell injection
            if not isinstance(video_path, str) or any(c in video_path for c in ";&|`$(){}[]<>*?!#~"):
                error_msg = "Invalid video path contains unsafe characters"
                raise ValueError(error_msg)

            # Process the video
            return self.process_video(video_path, self.clip_duration, include_original=self.include_original)

        except Exception as e:
            self.log(f"Error in split video component: {e!s}", "ERROR")
            raise
