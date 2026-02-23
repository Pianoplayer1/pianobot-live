from math import ceil

from discord import ButtonStyle, Interaction, Message, ui
from discord.abc import Messageable
from discord.ext.commands import Bot, Context


class Buttons(ui.View):
    def __init__(self, normal_pages: list[str], reversed_pages: list[str] | None = None) -> None:
        super().__init__(timeout=300)
        self.current_page = 0
        self.current_pages = normal_pages
        self.normal_pages = normal_pages
        self.reversed_pages = reversed_pages
        self.max_page = len(self.normal_pages) - 1
        self.message: Message | None = None
        if reversed_pages is None:
            self.remove_item(self.revert)

    async def handle_click(self, interaction: Interaction) -> None:
        self.current_page = min(max(self.current_page, 0), self.max_page)
        self.first_page.disabled = self.current_page == 0
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == self.max_page
        self.last_page.disabled = self.current_page == self.max_page
        await interaction.response.edit_message(
            content=self.current_pages[self.current_page],
            view=self,
        )

    async def on_timeout(self) -> None:
        content = (
            self.current_pages[self.current_page][:-3] + ' (Locked)```'
            if self.reversed_pages is None
            else self.current_pages[self.current_page][:-4] + ' - Locked)```'
        )
        if self.message is not None:
            await self.message.edit(content=content, view=None)

    @ui.button(disabled=True, emoji='⏮', style=ButtonStyle.gray)
    async def first_page(self, interaction: Interaction, _: ui.Button[ui.View]) -> None:
        self.current_page = 0
        await self.handle_click(interaction)

    @ui.button(disabled=True, emoji='◀', style=ButtonStyle.gray)
    async def previous_page(self, interaction: Interaction, _: ui.Button[ui.View]) -> None:
        self.current_page -= 1
        await self.handle_click(interaction)

    @ui.button(emoji='🔁', style=ButtonStyle.gray)
    async def revert(self, interaction: Interaction, _: ui.Button[ui.View]) -> None:
        self.current_pages = (
            self.reversed_pages
            if self.current_pages == self.normal_pages and self.reversed_pages is not None
            else self.normal_pages
        )
        await self.handle_click(interaction)

    @ui.button(emoji='▶', style=ButtonStyle.gray)
    async def next_page(self, interaction: Interaction, _: ui.Button[ui.View]) -> None:
        self.current_page += 1
        await self.handle_click(interaction)

    @ui.button(emoji='⏭', style=ButtonStyle.gray)
    async def last_page(self, interaction: Interaction, _: ui.Button[ui.View]) -> None:
        self.current_page = len(self.normal_pages) - 1
        await self.handle_click(interaction)


async def paginator(
    ctx: Messageable,
    data: list[list[str]],
    columns: dict[str, int],
    *,
    revert_option: bool = True,
    page_rows: int = 15,
    separator_rows: int = 5,
    enum: bool = True,
    message: Message | None = None,
    start_descending: bool = True,
    start_text: str | None = None,
) -> None:
    if revert_option:
        ascending_data = table(
            columns.copy(),
            data,
            separator_rows,
            page_rows,
            enum,
            '(Ascending Order)',
            start_text,
        )
        data.reverse()
        descending_data = table(
            columns,
            data,
            separator_rows,
            page_rows,
            enum,
            '(Descending Order)',
            start_text,
        )
        initial_data = descending_data if start_descending else ascending_data
        view = Buttons(descending_data, ascending_data) if len(descending_data) > 1 else None
    else:
        initial_data = table(columns, data, separator_rows, page_rows, enum)
        view = Buttons(initial_data) if len(initial_data) > 1 else None

    if message is None:
        if view is None:
            message = await ctx.send(initial_data[0])
        else:
            message = await ctx.send(initial_data[0], view=view)
    else:
        await message.edit(content=initial_data[0], view=view)

    if view is not None:
        view.message = message


def table(
    columns: dict[str, int],
    raw_data: list[list[str]],
    seperator: int = 0,
    page_len: int = 0,
    enum: bool = False,
    label: str | None = None,
    start_text: str | None = None,
) -> list[str]:
    if enum:
        columns[list(columns.keys())[0]] -= 5
    message = []
    count = 0
    page_num = 1 if page_len == 0 else ceil(len(raw_data) / page_len)
    for page in range(page_num):
        try:
            data = raw_data[page * page_len : (page + 1) * page_len]
        except IndexError:
            data = raw_data[page * page_len :]
        if len(data) == 0:
            data = raw_data[page * page_len :]
        message.append((start_text + '\n' if start_text else '') + '```ml\n│')

        if enum:
            message[page] += '     '
        for column in columns:
            message[page] += f' {column.ljust(columns[column] - 1)}│'

        for row in data:
            if count % page_len == 0 or seperator != 0 and (count - page * page_len) % seperator == 0:
                message[page] += '\n├'
                if enum:
                    message[page] += '─────'
                for pos, column in enumerate(columns):
                    message[page] += '─' * (columns[column]) + (
                        '┼' if pos != len(columns) - 1 else '┤'
                    )
            count += 1

            message[page] += '\n│'
            if enum:
                message[page] += f'{count}.'.rjust(5)
            for i in range(len(columns)):
                try:
                    message[page] += f' {str(row[i]).ljust(list(columns.values())[i] - 1)}│'
                except IndexError:
                    message[page] += ' ' * (list(columns.values())[i]) + '│'

        if page_num > 1:
            message[page] += f'\n\nPage {page + 1} / {page_num}'
            if label is not None:
                message[page] += f' {label}'
        message[page] += '```'

    return message
