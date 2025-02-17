# Construct a builder config file from the data in data/models-all.csv
import csv
import yaml
import copy

UC_ORDER = (
    "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z "
    "U+00C6 U+00D0 U+0132 U+014a U+0152 U+00DE U+1E9E".split()
)

LC_ORDER = (
    "a b c d e f g h i j k l m n o p q r s t u v w x y z "
    "U+00E6 U+00F0 U+0133 U+014B U+0153 U+00FE U+00DF U+0131 U+0237".split()
)

locl_required = {
    "CZ": "CSY",
    "ES": "ESP",
    "NL": "NLD",
    "RO": "ROM",
    "SK": "SKY",
}

added_values = set([0, -18])
slant_values = [
    {"name": "Regular", "value": 0},
    {"name": "Italic", "value": -18},
]

config = {
    "sources": ["Playwrite_MM.glyphspackage"],
    "doGuidelines": False,
    "buildStatic": True,
    "buildColorVariable": False,
    "recipeProvider": "fontprimer",
    "variants": [],
    "stat": [
        {
            "name": "Weight",
            "tag": "wght",
            "values": [
                {"name": "Thin", "value": 100},
                {"name": "ExtraLight", "value": 200},
                {"name": "Light", "value": 300},
                {"name": "Regular", "value": 400, "flags": 2},
            ],
        },
        {
            "name": "Slant",
            "tag": "slnt",
            "values": slant_values,
        },
        {"name": "Speed", "tag": "SPED"},
        {"name": "Y Extension", "tag": "YEXT"},
    ],
}

with open("sources/data/models-all.csv", "r") as file:
    reader = csv.DictReader(file, delimiter=";")
    for ix, model in enumerate(reader):
        new_ucs = model["UC"].strip().split()
        new_lcs = model["lc"].strip().split()

        mapping = {}
        for old, new in zip(UC_ORDER, new_ucs):
            mapping[old] = new
        for old, new in zip(LC_ORDER, new_lcs):
            mapping[old] = new
        # model_name = model["Country"]
        # if "_" in model["lang_tag"]:
        # model_name += " " + model["lang_tag"].split("_")[1]
        model_name = model["lang_tag"].replace("_", " ")
        remapLayout = []
        if model["lang_tag"] in locl_required:
            remapLayout = [
                {
                    "operation": "remapLayout",
                    "args": "'latn/"
                    + locl_required[model["lang_tag"]]
                    + "/locl => latn/dflt/locl'",
                }
            ]
        if "-" in model["slnt"]:
            regular, italic = model["slnt"].split("-")
            # Regular is easy
            config["variants"].append(
                {
                    "name": model_name,
                    "alias": model["lang_tag"].replace("_", " "),
                    "steps": remapLayout
                    + [
                        {
                            "operation": "subspace",
                            "axes": f"YEXT={model['YEXT']} SPED={model['SPED']} slnt={regular}",
                        },
                        {"operation": "remap", "args": "--deep", "mappings": mapping},
                        {
                            "operation": "remapLayout",
                            "args": "'locl=>|calt' 'ccmp=>|calt'",
                        },
                        {"operation": "hbsubset", "args": "--passthrough-tables"},
                        {"operation": "fix", "args": "--include-source-fixes"},
                        {"operation": "buildStat", "args": "--src stat.yaml"},
                    ],
                }
            )
            italic = -int(italic)
            config["variants"].append(
                {
                    "name": model_name,
                    "alias": model["lang_tag"].replace("_", " "),
                    "italic": True,
                    "steps": remapLayout
                    + [
                        {
                            "operation": "subspace",
                            "axes": f"YEXT={model['YEXT']} SPED={model['SPED']} slnt={italic}",
                            "args": "--update-name-table",
                        },
                        {
                            "operation": "remap",
                            "args": "--deep",
                            "mappings": copy.deepcopy(mapping),
                        },
                        {"operation": "hbsubset", "args": "--passthrough-tables"},
                        # Give italic VFs a better STAT
                        {"operation": "buildStat", "args": "--src stat-italic.yaml"},
                        {"operation": "fix", "args": "--include-source-fixes"},
                    ],
                }
            )
            # Add the italic value to the stat table
            if italic not in added_values:
                added_values.add(italic)
                slant_values.append(
                    {"name": "Italic", "value": int(italic)},
                )

        else:
            config["variants"].append(
                {
                    "name": model_name,
                    "alias": model["lang_tag"].replace("_", " "),
                    "steps": remapLayout
                    + [
                        {
                            "operation": "subspace",
                            "axes": f"YEXT={model['YEXT']} SPED={model['SPED']} slnt=-{model['slnt']}",
                        },
                        {"operation": "remap", "args": "--deep", "mappings": mapping},
                        {
                            "operation": "remapLayout",
                            "args": "'locl=>|calt' 'ccmp=>|calt'",
                        },
                        {"operation": "hbsubset", "args": "--passthrough-tables"},
                        {
                            "operation": "buildStat",
                            "args": "--src stat-standalone.yaml",
                        },
                        {"operation": "fix", "args": "--include-source-fixes"},
                        {
                            "operation": "exec",
                            "exe": "gftools-fontsetter",
                            "args": "-o $out $in zero-post.yaml",
                        },
                    ],
                }
            )
            # I hate this
            italic = -int(model["slnt"])
            if italic not in added_values:
                added_values.add(italic)
                slant_values.append(
                    {"name": "Italic", "value": italic},
                )

with open("sources/config.yaml", "w") as file:
    yaml.dump(config, file, sort_keys=False, default_flow_style=False)
