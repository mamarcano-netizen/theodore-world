import time
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

console = Console(force_terminal=True, highlight=False)

console.clear()
console.print()
console.print("  [#1B1F3B on #7B5EA7]                                              [/]")
console.print("  [#1B1F3B on #7B5EA7]   THEODORE'S WORLD — Image Uploader  🦸🦋   [/]")
console.print("  [#1B1F3B on #7B5EA7]       theodore-world.com               🧩   [/]")
console.print("  [#1B1F3B on #7B5EA7]                                              [/]")
console.print("  [italic #6EC6F5]Different isn't just okay. Different is a superpower. 💙[/]\n")
time.sleep(0.8)

console.rule("[bold #7B5EA7]  Finding Images  [/]")
console.print(Panel(
    "  [bold #FFD166]1.[/bold #FFD166]  0_3YUYUI.jpeg\n"
    "  [bold #FFD166]2.[/bold #FFD166]  SuperTheoOfficial.jpg\n"
    "  [bold #FFD166]3.[/bold #FFD166]  theo-butterfly.jpg",
    title="[bold #7B5EA7]  Images Found on Desktop  [/]",
    border_style="#7B5EA7",
    box=box.ROUNDED
))

console.print("\n  [bold #FFD166]Selected:[/]  0_3YUYUI.jpeg\n")
time.sleep(0.5)

console.print(Panel(
    "  [bold #6EC6F5]6.[/bold #6EC6F5]   Chapter 3 — Flutter's Powers\n"
    "  [bold #6EC6F5]7.[/bold #6EC6F5]   Chapter 4 — Amazing Powers\n"
    "  [bold #6EC6F5]14.[/bold #6EC6F5]  Chapter 7 — The Spectrum Burst  [dim]<-- selected[/dim]",
    title="[bold #7B5EA7]  Storybook Pages  [/]",
    border_style="#6EC6F5",
    box=box.ROUNDED
))

console.print(f"\n  [bold #FFD166]Image:[/]  0_3YUYUI.jpeg")
console.print(f"  [bold #FFD166]Page:[/]   Chapter 7 — The Spectrum Burst")
console.print(f"  [bold #FFD166]File:[/]   theo-celebrating.jpg\n")
time.sleep(0.5)

console.rule("[bold #7B5EA7]  Step 1 — Copying Image  [/]")
with Progress(
    SpinnerColumn(style="#7B5EA7"),
    TextColumn("[bold #FFD166]Copying to Theodore's World..."),
    BarColumn(bar_width=30, complete_style="#7B5EA7", finished_style="#FFD166"),
    console=console
) as progress:
    task = progress.add_task("copy", total=100)
    for _ in range(100):
        time.sleep(0.015)
        progress.update(task, advance=1)
console.print("  [green]Copied![/green] [dim]theo-celebrating.jpg[/dim]\n")
time.sleep(0.3)

console.rule("[bold #7B5EA7]  Step 2 — Updating Website  [/]")
with Progress(
    SpinnerColumn(spinner_name="dots", style="#6EC6F5"),
    TextColumn("[bold #FFD166]Updating storybook page..."),
    console=console
) as progress:
    task = progress.add_task("update", total=None)
    for _ in range(25):
        time.sleep(0.06)
        progress.update(task, advance=1)
console.print("  [green]Page updated:[/green] [dim]Chapter 7 — The Spectrum Burst[/dim]\n")
time.sleep(0.3)

console.rule("[bold #7B5EA7]  Step 3 — Deploying to Website  [/]")
with Progress(
    SpinnerColumn(spinner_name="dots2", style="#FF8FAB"),
    TextColumn("[bold #FFD166]Pushing to theodore-world.com..."),
    console=console
) as progress:
    task = progress.add_task("deploy", total=None)
    for _ in range(30):
        time.sleep(0.07)
        progress.update(task, advance=1)
console.print("  [green]Live on theodore-world.com![/green]\n")
time.sleep(0.3)

console.print(Panel(
    Align.center(
        Text.assemble(
            ("\n  IMAGE IS LIVE ON THE WEBSITE!  \n\n", "bold #FFD166"),
            ("theodore-world.com\n", "bold #7B5EA7"),
            ("Chapter 7 — The Spectrum Burst\n\n", "bold #6EC6F5"),
        )
    ),
    border_style="#FFD166",
    box=box.DOUBLE,
))

table = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
table.add_column(style="bold #FFD166", no_wrap=True)
table.add_column(style="white")
table.add_row("Image", "0_3YUYUI.jpeg")
table.add_row("Page", "Chapter 7 — The Spectrum Burst")
table.add_row("Live at", "theodore-world.com")
table.add_row("Deploy", "Auto-deployed via Netlify")
console.print(table)
console.print(f"\n  [italic #6EC6F5]Different is a superpower. 💙🧩🌈[/]\n")
