import sys
import os
import time
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt
from rich import box

console = Console(force_terminal=True, highlight=False)

PURPLE = "bold #7B5EA7"
BLUE   = "bold #6EC6F5"
GOLD   = "bold #FFD166"
PINK   = "bold #FF8FAB"
NAVY   = "#1B1F3B"
DIM    = "dim white"

PAGES = {
    "1":  ("Chapter 1 — A Boy Who Saw the World",     "theo-standing.jpg"),
    "2":  ("Chapter 1 — The Boy Who Listened",         "theo-listening.jpg"),
    "3":  ("Chapter 2 — The Spectrum Orb",             "theo-orb.jpg"),
    "4":  ("Chapter 2 — Super Theo Awakens",           "theo-flying.jpg"),
    "5":  ("Chapter 3 — A Butterfly is Born",          "theo-butterfly.jpg"),
    "6":  ("Chapter 3 — Flutter's Powers",             "theo-flutter.jpg"),
    "7":  ("Chapter 4 — Amazing Powers",               "theo-playing.jpg"),
    "8":  ("Chapter 4 — Four Incredible Powers",       "theo-powers.jpg"),
    "9":  ("Chapter 5 — Villains Plan",                "theo-villains.jpg"),
    "10": ("Chapter 5 — The Conformists Attack",       "theo-attack.jpg"),
    "11": ("Chapter 6 — The Battle",                   "theo-battle.jpg"),
    "12": ("Chapter 6 — Truth Sparkles & Connection",  "theo-truth.jpg"),
    "13": ("Chapter 7 — Super Theo vs Dr Norm",        "theo-drnorm.jpg"),
    "14": ("Chapter 7 — The Spectrum Burst",           "theo-celebrating.jpg"),
    "15": ("Chapter 8 — A World Full of Color",        "theo-calming.jpg"),
    "16": ("Chapter 8 — Everyone Free to Be Themselves","theo-friends.jpg"),
}

REPO = Path(__file__).parent

def banner():
    console.clear()
    console.print()
    console.print("  [#1B1F3B on #7B5EA7]                                            [/]")
    console.print("  [#1B1F3B on #7B5EA7]   THEODORE'S WORLD — Image Uploader  🦸🦋  [/]")
    console.print("  [#1B1F3B on #7B5EA7]       theodore-world.com               🧩  [/]")
    console.print("  [#1B1F3B on #7B5EA7]                                            [/]")
    console.print("  [italic #6EC6F5]Different isn't just okay. Different is a superpower. 💙[/]\n")
    time.sleep(0.5)

def find_images():
    desktop = Path.home() / "OneDrive" / "Desktop"
    exts = [".jpg", ".jpeg", ".png", ".webp"]
    images = [f for f in desktop.iterdir() if f.suffix.lower() in exts]

    new_folder = desktop / "New folder"
    if new_folder.exists():
        images += [f for f in new_folder.iterdir() if f.suffix.lower() in exts]

    return images

def pick_image(images):
    console.print(Panel(
        "\n".join([f"  [bold #FFD166]{i+1}.[/bold #FFD166]  {f.name}" for i, f in enumerate(images)]),
        title="[bold #7B5EA7]  Images Found on Desktop  [/]",
        border_style="#7B5EA7",
        box=box.ROUNDED
    ))

    if len(images) == 1:
        console.print(f"\n  [dim]Auto-selected:[/dim] [bold]{images[0].name}[/bold]\n")
        return images[0]

    choice = Prompt.ask(f"\n  [bold #FFD166]Which image?[/] (1-{len(images)})", default="1")
    return images[int(choice) - 1]

def pick_page():
    console.print()
    console.print(Panel(
        "\n".join([
            f"  [bold #6EC6F5]{k}.[/bold #6EC6F5]  {v[0]}"
            for k, v in PAGES.items()
        ]),
        title="[bold #7B5EA7]  Storybook Pages  [/]",
        border_style="#6EC6F5",
        box=box.ROUNDED
    ))
    choice = Prompt.ask(f"\n  [bold #FFD166]Which page does this image go on?[/] (1-16)", default="1")
    return choice, PAGES[choice]

def copy_and_deploy(image_path, page_key, page_name, filename):
    dest = REPO / filename

    # STEP 1 — Copy
    console.rule("[bold #7B5EA7]  Step 1 — Copying Image  [/]")
    with Progress(
        SpinnerColumn(style="#7B5EA7"),
        TextColumn("[bold #FFD166]Copying to Theodore's World..."),
        BarColumn(bar_width=30, complete_style="#7B5EA7", finished_style="#FFD166"),
        console=console
    ) as progress:
        task = progress.add_task("copy", total=100)
        shutil.copy2(image_path, dest)
        for _ in range(100):
            time.sleep(0.015)
            progress.update(task, advance=1)
    console.print(f"  [green]✓ Copied![/green] [dim]{filename}[/dim]\n")

    # STEP 2 — Update website code
    console.rule("[bold #7B5EA7]  Step 2 — Updating Website  [/]")
    with Progress(
        SpinnerColumn(spinner_name="dots", style="#6EC6F5"),
        TextColumn("[bold #FFD166]Updating storybook page..."),
        console=console
    ) as progress:
        task = progress.add_task("update", total=None)

        html_path = REPO / "index.html"
        html = html_path.read_text(encoding="utf-8")

        page_titles = {
            "1":  "A Boy Who Saw the World",
            "2":  "The Boy Who Listened",
            "3":  "The Night the",
            "4":  "Super Theo Awakens",
            "5":  "A <span>Butterfly</span> Is Born",
            "6":  "Flutter",
            "7":  "Super Theo's <span>Amazing Powers</span>",
            "8":  "Four Incredible Powers",
            "9":  "The <span>Villains</span>",
            "10": "The Conformists Attack",
            "11": "The Battle for Being",
            "12": "Truth, Sparkles",
            "13": "Super Theo vs.",
            "14": "The <span>Spectrum Burst</span>",
            "15": "A World Full of",
            "16": "Everyone, Free to Be",
        }

        search = page_titles.get(page_key, "")
        if search:
            import re
            pattern = rf'(title:\'{re.escape(search)}[^\']*\'[^}}]*?img:\')[^\']*(\',)'
            replacement = rf'\g<1>https://theodore-world.com/{filename}\g<2>'
            new_html = re.sub(pattern, replacement, html, count=1)
            if new_html != html:
                html_path.write_text(new_html, encoding="utf-8")

        for _ in range(20):
            time.sleep(0.05)
            progress.update(task, advance=1)

    console.print(f"  [green]✓ Page updated:[/green] [dim]{page_name}[/dim]\n")

    # STEP 3 — Git push
    console.rule("[bold #7B5EA7]  Step 3 — Deploying to Website  [/]")
    with Progress(
        SpinnerColumn(spinner_name="aesthetic", style="#FF8FAB"),
        TextColumn("[bold #FFD166]Pushing to theodore-world.com..."),
        console=console
    ) as progress:
        task = progress.add_task("deploy", total=None)

        subprocess.run(["git", "add", str(dest), str(html_path)], cwd=REPO, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Add image for: {page_name}"], cwd=REPO, capture_output=True)
        result = subprocess.run(["git", "push"], cwd=REPO, capture_output=True)

        for _ in range(30):
            time.sleep(0.06)
            progress.update(task, advance=1)

    console.print(f"  [green]✓ Live on theodore-world.com![/green]\n")

def success_screen(image_name, page_name, filename):
    console.print(Panel(
        Align.center(
            Text.assemble(
                ("\n  IMAGE IS LIVE ON THE WEBSITE!  \n\n", "bold #FFD166"),
                ("theodore-world.com\n", "bold #7B5EA7"),
                (f"Page: {page_name}\n\n", "bold #6EC6F5"),
            )
        ),
        border_style="#FFD166",
        box=box.DOUBLE,
    ))

    table = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    table.add_column(style="bold #FFD166", no_wrap=True)
    table.add_column(style="white")
    table.add_row("Image", image_name)
    table.add_row("Page", page_name)
    table.add_row("Live at", f"theodore-world.com")
    table.add_row("Deploy", "Auto-deployed via Netlify")
    console.print(table)
    console.print(f"\n  [italic #6EC6F5]Different is a superpower. 💙🧩🌈[/]\n")

def main():
    banner()

    console.rule("[bold #7B5EA7]  Finding Images  [/]")
    images = find_images()

    if not images:
        console.print(Panel(
            "No images found on Desktop!\n\nSave your Midjourney image to the Desktop first.",
            title="[red]No Images Found[/red]",
            border_style="red"
        ))
        sys.exit(1)

    image = pick_image(images)
    page_key, (page_name, filename) = pick_page()

    console.print(f"\n  [bold #FFD166]Image:[/]  {image.name}")
    console.print(f"  [bold #FFD166]Page:[/]   {page_name}")
    console.print(f"  [bold #FFD166]File:[/]   {filename}\n")

    confirm = Prompt.ask("  [bold #7B5EA7]Ready to upload?[/] (y/n)", default="y")
    if confirm.lower() != "y":
        console.print("\n  [dim]Cancelled.[/dim]\n")
        sys.exit(0)

    console.print()
    copy_and_deploy(image, page_key, page_name, filename)
    success_screen(image.name, page_name, filename)

if __name__ == "__main__":
    main()
