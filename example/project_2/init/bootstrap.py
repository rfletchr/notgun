import notgun.projects
import notgun.templates
import notgun.launcher
import notgun.bootstrap
import notgun.workareas


def bootstrap(data) -> notgun.projects.Project:
    identifier = notgun.templates.Token.identifier()
    version = notgun.templates.Token.integer(padding=3)

    tokens: dict[str, notgun.templates.Token] = {
        "project": identifier,
        "sequence": identifier,
        "shot": identifier,
        "shot_task": identifier,
        "asset_type": identifier,
        "asset": identifier,
        "task": identifier,
        "app": identifier,
        "name": identifier,
        "version": version,
        "ext": identifier,
    }

    template_defs: dict[str, str] = {
        "project": "{project}",
        "sequence": "<project>/sequences/{sequence}",
        "asset_type": "<project>/assets/{asset_type}",
        "shot": "<sequence>/{shot}",
        "asset": "<asset_type>/assets/{asset}",
        "shot_task": "<shot>/work/{task}",
        "shot_workarea": "<shot_task>/{app}",
        "shot_workfile": "<shot_workarea>/{name}.v{version}.{ext}",
        "asset_task": "<asset>/tasks/{task}",
        "asset_workarea": "<asset_task>/{app}",
    }

    templates = notgun.templates.compile_path_templates(
        data.projects_dir,
        template_defs,
        tokens,
    )

    programs = {
        "nuke": notgun.launcher.Program(
            "Nuke",
            "rez",
            ["env", "notgun-nuke", "--", "nuke"],
        ),
        "maya": notgun.launcher.Program(
            "Maya", "rez", ["env", "notgun-maya", "--", "maya"]
        ),
    }

    workarea_type = notgun.workareas.WorkAreaType(
        label="Workarea",
        template=templates["shot_workarea"],
        token="app",
        children=[],
        workfiles_template=templates["shot_workfile"],
    )

    task_type = notgun.workareas.WorkAreaType(
        label="Task",
        template=templates["shot_task"],
        token="task",
        children=[workarea_type],
    )
    shot_type = notgun.workareas.WorkAreaType(
        label="Shot",
        template=templates["shot"],
        token="shot",
        children=[task_type],
    )
    sequence_type = notgun.workareas.WorkAreaType(
        label="Sequence",
        template=templates["sequence"],
        token="sequence",
        children=[shot_type],
    )
    project_type = notgun.workareas.WorkAreaType(
        label="Project",
        template=templates["project"],
        token="project",
        children=[sequence_type],
    )

    fields = {"project": data.project_name}
    root_location = notgun.workareas.WorkArea(
        project_type,
        data.project_name,
        templates["project"].format(fields),
        fields,
    )

    return notgun.projects.Project(
        data.projects_dir,
        data.project_name,
        templates,
        notgun.projects.DEFAULT_CONTEXT_NAMES,
        programs,
        root_location,
    )
