#!/usr/bin/env python3
"""
OpenBioMed 初始化脚本
在 Open WebUI 启动时自动导入预置 skills
"""

import os
import sys
import shutil
import asyncio
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

import yaml
from open_webui.models.skills import Skills, SkillForm, SkillMeta


def parse_frontmatter(content: str):
    """解析 markdown 文件的 frontmatter"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_text = parts[1].strip()
    body = parts[2].strip()

    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except Exception:
        metadata = {}

    return metadata, body


def apply_branding():
    """用 OpenBioMed 品牌资源覆盖后端 STATIC_DIR 的默认文件"""
    assets_dir = Path(__file__).parent / 'assets'
    if not assets_dir.exists():
        print("Assets directory not found, skipping branding")
        return

    from open_webui.config import STATIC_DIR

    # favicon.png 和 logo.png 有独立源文件，其余用 logo.png 作为源
    branding_map = {
        'favicon.png': assets_dir / 'favicon.png',
        'logo.png': assets_dir / 'logo.png',
        'splash.png': assets_dir / 'logo.png',
        'favicon-dark.png': assets_dir / 'logo.png',
        'splash-dark.png': assets_dir / 'logo.png',
    }

    for dst_name, src_path in branding_map.items():
        dst_path = STATIC_DIR / dst_name
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"Branding: {src_path.name} -> {dst_path}")


def ensure_signup_enabled():
    """确保 signup 保持开启（兜底防自动关闭）"""
    from open_webui.config import AppConfig
    import sqlite3, json

    db_path = Path(os.environ.get('DATA_DIR', '/app/data')) / 'webui.db'
    if not db_path.exists():
        print("Database not found, skipping signup enforcement")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM config WHERE id=1')
    row = cursor.fetchone()
    if row:
        data = json.loads(row[0])
        if data.get('ui', {}).get('enable_signup') is not True:
            data.setdefault('ui', {})['enable_signup'] = True
            cursor.execute('UPDATE config SET data=? WHERE id=1', (json.dumps(data),))
            conn.commit()
            print("Signup: forced enable_signup=True in database")
    conn.close()


async def init_skills():
    """初始化预置 skills"""
    skills_dir = Path(__file__).parent / 'skills'

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        return

    # 查找所有 SKILL.md 文件
    skill_files = list(skills_dir.glob('*/SKILL.md'))

    if not skill_files:
        print("No skills found to import")
        return

    print(f"Found {len(skill_files)} skills to import")

    for skill_file in skill_files:
        try:
            content = skill_file.read_text()
            metadata, body = parse_frontmatter(content)

            skill_id = metadata.get('name', skill_file.parent.name)
            skill_name = metadata.get('name', skill_file.parent.name)
            skill_description = metadata.get('description', '')
            tags = metadata.get('tags', [])

            # 构建完整的 skill content（包含 frontmatter）
            full_content = content

            # 创建 skill form
            form_data = SkillForm(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                content=full_content,
                meta=SkillMeta(tags=tags if isinstance(tags, list) else []),
                is_active=True,
                access_grants=[]
            )

            # 检查 skill 是否已存在
            existing = await Skills.get_skill_by_id(skill_id)
            if existing:
                print(f"Skill '{skill_id}' already exists, updating...")
                await Skills.update_skill_by_id(skill_id, {
                    'name': skill_name,
                    'description': skill_description,
                    'content': full_content,
                    'meta': form_data.meta.model_dump()
                })
            else:
                print(f"Creating skill '{skill_id}'...")
                await Skills.insert_new_skill(
                    user_id='system',  # 使用 system 用户
                    form_data=form_data
                )

        except Exception as e:
            print(f"Error importing skill {skill_file}: {e}")
            continue

    print("Skills initialization complete")


async def main():
    """主入口"""
    print("OpenBioMed initialization script starting...")
    apply_branding()
    ensure_signup_enabled()
    await init_skills()
    print("OpenBioMed initialization complete")


if __name__ == '__main__':
    asyncio.run(main())
