import notgun.pipeline
import notgun.templates
import notgun.launcher
import notgun.bootstrap


def bootstrap(data) -> notgun.pipeline.Pipeline:
    identifier = notgun.templates.Token.identifier()
    tokens: dict[str, notgun.templates.Token] = {
        "project": identifier,
        "sequence": identifier,
        "shot": identifier,
        "shot_task": identifier,
        "asset_type": identifier,
        "asset": identifier,
        "task": identifier,
    }

    template_defs: dict[str, str] = {
        "project": "{project}",
        "sequence": "<project>/sequences/{sequence}",
        "asset_type": "<project>/assets/{asset_type}",
        "shot": "<sequence>/shots/{shot}",
        "asset": "<asset_type>/assets/{asset}",
        "shot_task": "<shot>/tasks/{task}",
        "asset_task": "<asset>/tasks/{task}",
    }

    path_templates = notgun.templates.compile_path_templates(
        data.projects_dir,
        template_defs,
        tokens,
    )

    programs = {
        "nuke": notgun.launcher.Program(
            "Nuke",
            "rez",
            ["env", "notgun-nuke"],
        ),
    }

    return notgun.pipeline.Pipeline(
        data.projects_dir,
        data.project_name,
        path_templates,
        notgun.pipeline.DEFAULT_CONTEXT_NAMES,
        programs,
    )
