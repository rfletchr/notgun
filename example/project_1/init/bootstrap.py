import notgun.projects
import notgun.templates
import notgun.launcher
import notgun.workareas
import notgun.bootstrap
import notgun.schema


def bootstrap(data: notgun.bootstrap.BootstrapData) -> notgun.projects.Project:
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
        "extension": identifier,
    }

    template_defs: dict[str, str] = {
        "project": "{project}",
        "sequences": "<project>/sequences",
        "sequence": "<sequences>/{sequence}",
        "assets": "<project>/assets",
        "asset_type": "<assets>/{asset_type}",
        "shot": "<sequence>/{shot}",
        "asset": "<asset_type>/assets/{asset}",
        "shot_task": "<shot>/work/{task}",
        "shot_workarea": "<shot_task>/{app}",
        "shot_workfile": "<shot_workarea>/{name}.v{version}.{extension}",
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
            ["env", "notgun_nuke", "--", "nuke"],
            ["nk"],
        ),
    }

    project_schema = notgun.schema.WorkareaSchema(
        label="Project",
        template=templates["project"],
        identity_token="project",
    )

    sequences_schema = project_schema.add_child(
        "Sequences",
        templates["sequences"],
    )
    sequence_schema = sequences_schema.add_child(
        "Sequence",
        templates["sequence"],
        identity_token="sequence",
    )
    shot_schema = sequence_schema.add_child(
        "Shot",
        templates["shot"],
        identity_token="shot",
    )
    shot_task_schema = shot_schema.add_child(
        "Task",
        templates["shot_task"],
        identity_token="task",
    )
    shot_workarea_schema = shot_task_schema.add_child(
        "Workarea",
        templates["shot_workarea"],
        identity_token="app",
    )
    shot_workarea_schema.add_workfile(
        "Nuke Script",
        templates["shot_workfile"],
        programs["nuke"],
        "{shot}_{task}",
        "nk",
    )

    project_schema.add_child("Assets", templates["assets"])

    return notgun.projects.Project(
        data.projects_dir,
        data.project_name,
        templates,
        programs,
        project_schema,
    )
