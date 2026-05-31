"""Static skill lint (no model, no network) — layer A of the skill test framework.

Validates each skill *as a skill*, not just its code:
- SKILL.md has well-formed frontmatter with `name` (matching the folder) and a
  non-empty `description`;
- every `scripts/<file>.py` the SKILL.md references actually exists;
- every bundled script imports cleanly (which exercises the shared-lib discovery,
  i.e. that `import mtg_scryfall` resolves via the `../../../lib` plugin layout).

Catches the realistic breakage — a SKILL.md pointing at a moved script, a malformed
frontmatter, or a broken lib path — entirely in CI, with no API key.
"""

import importlib.util
import os
import re
import sys
import unittest

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_SKILLS_DIR = os.path.join(_ROOT, "mtg-skills", "skills")


def _skill_dirs():
    return sorted(
        os.path.join(_SKILLS_DIR, d)
        for d in os.listdir(_SKILLS_DIR)
        if os.path.isfile(os.path.join(_SKILLS_DIR, d, "SKILL.md"))
    )


def _frontmatter(md_text):
    """Minimal YAML-frontmatter parse (stdlib only): returns {name, description}.

    The skills use only `name:` and a folded `description:`; we don't need a full YAML
    parser, just the two fields and the block boundaries.
    """
    if not md_text.startswith("---"):
        return None
    end = md_text.find("\n---", 3)
    if end == -1:
        return None
    block = md_text[3:end].strip("\n")
    name = None
    name_m = re.search(r"^name:\s*(.+?)\s*$", block, re.MULTILINE)
    if name_m:
        name = name_m.group(1).strip()
    # description: everything from the description: key to the end of the block,
    # with the key and folding markers stripped — we only measure presence/length.
    desc = ""
    dm = re.search(r"^description:\s*(.*)$", block, re.MULTILINE | re.DOTALL)
    if dm:
        desc = re.sub(r"^\s*>-?\s*", "", dm.group(1)).strip()
        desc = " ".join(line.strip() for line in desc.splitlines() if line.strip())
    return {"name": name, "description": desc}


class SkillLintTests(unittest.TestCase):
    def test_skills_present(self):
        dirs = _skill_dirs()
        self.assertTrue(dirs, "no skills found under mtg-skills/skills/")

    def test_frontmatter_valid(self):
        for d in _skill_dirs():
            with self.subTest(skill=os.path.basename(d)):
                with open(os.path.join(d, "SKILL.md"), encoding="utf-8") as fh:
                    fm = _frontmatter(fh.read())
                self.assertIsNotNone(fm, "SKILL.md missing/invalid frontmatter block")
                self.assertEqual(fm["name"], os.path.basename(d),
                                 "frontmatter name must match the skill folder name")
                self.assertTrue(fm["description"], "description is empty")

    def test_referenced_scripts_exist(self):
        for d in _skill_dirs():
            with open(os.path.join(d, "SKILL.md"), encoding="utf-8") as fh:
                body = fh.read()
            for rel in set(re.findall(r"scripts/([A-Za-z0-9_\-]+\.py)", body)):
                with self.subTest(skill=os.path.basename(d), script=rel):
                    self.assertTrue(os.path.isfile(os.path.join(d, "scripts", rel)),
                                    f"SKILL.md references scripts/{rel} which does not exist")

    def test_bundled_scripts_import(self):
        for d in _skill_dirs():
            scripts = os.path.join(d, "scripts")
            if not os.path.isdir(scripts):
                continue
            for fn in sorted(os.listdir(scripts)):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(scripts, fn)
                modname = f"_skilltest_{os.path.basename(d)}_{fn[:-3]}".replace("-", "_")
                with self.subTest(skill=os.path.basename(d), script=fn):
                    spec = importlib.util.spec_from_file_location(modname, path)
                    mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)  # runs top-level imports (lib discovery)
                    except Exception as e:  # noqa: BLE001 - any import failure is a lint failure
                        self.fail(f"{os.path.basename(d)}/scripts/{fn} failed to import: {e}")
                    finally:
                        sys.modules.pop(modname, None)


if __name__ == "__main__":
    unittest.main()
