import os
import notgun.bootstrap
import notgun.workareas


projects_dir = os.path.dirname(__file__)
project_name = "project_1"

data = notgun.bootstrap.BootstrapData(projects_dir, project_name)

pipeline = notgun.bootstrap.init(data)

for child in pipeline.workarea().iter_workareas():
    print(child)

print("#" * 80)

some_path = os.path.join(projects_dir, "project_1/sequences/JP_002/JP_002_0020")
location = notgun.workareas.workarea_from_path(some_path, pipeline.workarea().type)

print(location)
