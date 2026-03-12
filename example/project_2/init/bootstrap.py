import notgun.projects
import notgun.templates
import notgun.launcher
import notgun.workareas
import notgun.bootstrap


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
        "ext": identifier,
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
            "Nuke", "rez", ["env", "notgun-nuke", "--", "nuke"], ["nk"]
        ),
        "maya": notgun.launcher.Program(
            "Maya", "rez", ["env", "notgun-maya", "--", "maya"], ["ma", "mb"]
        ),
    }

    shot_workfile = notgun.workareas.WorkfileSchema(
        template=templates["shot_workfile"],
        programs=[programs["nuke"]],
        default_name="{shot}_{task}",
        default_extension="nk",
    )

    shot_workarea_schema = notgun.workareas.WorkareaSchema(
        label="Workarea",
        template=templates["shot_workarea"],
        token="app",
        workareas=[],
        workfile=shot_workfile,
        icon_name="ph.files-fill",
    )

    shot_task_schema = notgun.workareas.WorkareaSchema(
        label="Task",
        template=templates["shot_task"],
        token="task",
        workareas=[shot_workarea_schema],
        icon_name="ri.todo-line",
    )

    shot_schema = notgun.workareas.WorkareaSchema(
        label="Shot",
        template=templates["shot"],
        token="shot",
        workareas=[shot_task_schema],
        icon_name="mdi.filmstrip-box",
    )
    sequence_schema = notgun.workareas.WorkareaSchema(
        label="Sequence",
        template=templates["sequence"],
        token="sequence",
        workareas=[shot_schema],
        icon_name="mdi.filmstrip-box-multiple",
    )

    sequences_schema = notgun.workareas.WorkareaSchema(
        label="Sequences",
        template=templates["sequences"],
        token=None,
        workareas=[sequence_schema],
        icon_name="mdi.filmstrip-box-multiple",
    )

    assets_schema = notgun.workareas.WorkareaSchema(
        label="Assets",
        template=templates["assets"],
        token=None,
        workareas=[],
        icon_name="ph.cubes-fill",
    )

    project_schema = notgun.workareas.WorkareaSchema(
        label="Project",
        template=templates["project"],
        token="project",
        workareas=[sequences_schema, assets_schema],
    )

    fields: dict[str, str | int] = {"project": data.project_name}
    root_workarea = notgun.workareas.WorkArea(
        project_schema,
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
        root_workarea,
    )
