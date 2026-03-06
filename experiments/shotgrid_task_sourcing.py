import time
import notgun.credentials

credentials = notgun.credentials.get_credentials(
    "https://elephant-goldfish.shotgrid.autodesk.com"
)

if credentials is None:
    raise RuntimeError("Failed to authenticate with ShotGrid.")


sg = notgun.credentials.shotgun_api3.Shotgun(
    credentials.site_url,
    session_token=credentials.session_token,
)

start = time.time()
all_tasks = sg.find(
    "Task",
    [
        ["sg_status_list", "is_not", "omt"],
    ],
    [
        "content",
        "project",
        "entity",
        "sg_status_list",
    ],
)

shot_ids = set()
asset_ids: set[int] = set()
for task in all_tasks:
    entity = task.get("entity")
    if not entity:
        continue

    if entity["type"] == "Shot":
        shot_ids.add(entity["id"])
    elif entity["type"] == "Asset":
        asset_ids.add(entity["id"])

assets = sg.find("Asset", [["id", "in", list(asset_ids)]], ["code"])
shots = sg.find("Shot", [["id", "in", list(shot_ids)]], ["code"])


end = time.time()
print(f"Retrieved {len(all_tasks)} tasks in {end - start:.2f} seconds.")
print(f"Unique shots: {len(shot_ids)}, Unique assets: {len(asset_ids)}")
