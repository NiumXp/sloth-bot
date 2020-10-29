import discord
from discord.ext import commands
import os
from datetime import datetime
from PIL import Image, ImageFont, ImageDraw
from typing import Tuple
import aiohttp
from io import BytesIO
import shutil
import json
import asyncio
from zipfile import ZipFile
from typing import Dict, List, Union


class TeacherAPI(commands.Cog):
	""" (WIP) A category for using The Language Sloth's teacher's API, 
	and some other useful commands related to it. """
	def __init__(self, client) -> None:
		""" Cog initializer """

		self.client = client
		self.teacher_role_id: int = 507298235766013981
		self.session = aiohttp.ClientSession(loop=client.loop)
		self.classes_channel_id: int = 689918515129352213
		self.website_link: str = 'https://languagesloth.herokuapp.com/api/teachers/?format=json'


	@commands.Cog.listener()
	async def on_ready(self) -> None:
		""" For when the bot starts up """

		print('Tests cog is online!')

	async def get_flag(self, language: str) -> str:
		""" Gets a flag from the media files. 
		:param language: The language related to the flag.
		:returns: The path of the requested flag, or of the default one.
		"""
	
		path = f"./media/flags/{language.lower()}.png"
		if os.path.isfile(path):
			return path
		else:
			return f"./media/flags/default.png"


	async def paste_text(self, draw, coords: Tuple[int], text: str, color: Tuple[int], font, stroke: Tuple[int]) -> None:
		""" Pastes the given text making a nifty stroke around it. 
		:param draw: The draw object to paste on.
		:param coords: The image coordinates to paste on.
		:param text: The text to write in the image.
		:param color: The text color.
		:param stroke: The stroke color.
		"""
		
		draw.text((coords[0]-1, coords[1]), text, stroke, font=font) # Left
		draw.text((coords[0]+1, coords[1]), text, stroke, font=font) # Right
		draw.text((coords[0], coords[1]-1), text, stroke, font=font) # Top
		draw.text((coords[0], coords[1]+1), text, stroke, font=font) # Bottom
		draw.text((coords[0], coords[1]), text, color, font=font) # Center


	async def make_description(self, description: str) -> str:
		""" Rearranges the given text by adding \\n tags every 29 characters
		to fit properly in the image.
		:param description: The description rearrange.
		:returns: The rearranged description.
		"""
		new_description = ''
		i = 0
		for l in description:
			i += 1
			if i == 29:
				new_description += '\n'
				i = 0
			if i == 0 and l == ' ':
				continue
			new_description += l

		return new_description

	async def get_teacher_pfp(self, teacher: discord.Member) -> Image:
		""" Gets the given teacher's profile picture and returns it.
		:param teacher: The teacher from whom to get the profile picture.
		:returns: The teacher's profile picture in a Pillow Image object.
		"""
		async with self.session.get(str(teacher.avatar_url)) as response:
			image_bytes = await response.content.read()
			with BytesIO(image_bytes) as pfp:
				image = Image.open(pfp)
				width, height = image.size
				if width > 128 or height > 128:
					image = image.resize((128, 128))

				im = image.convert('RGBA')
				return im


	@commands.command(aliases=['mc', 'card'])
	@commands.has_permissions(kick_members=True)
	async def make_card(self, ctx, teacher: discord.Member = None, language: str = None, description: str = None, weekday: str = None, time: str = None) -> None:
		""" Makes a teacher card with their class information.
		:param teacher: The teacher for whom to make the card.
		:param language: The teacher's class language.
		:param description: The teacher's class description.
		:param weekday: The day of the teacher's class.
		:param time: The time of the teacher's class.
		"""

		# Checks if the command was given all the required information to make the card.
		
		author = ctx.author
		try:
			assert teacher, await ctx.send(f"**Please, {author.mention}, inform the `teacher`!**")
			assert description, await ctx.send(f"**Please, {author.mention}, inform the `description`!**")
			assert len(description) < 75, await ctx.send(f"**Please, {author.mention}, the `description` must be under 76 characters!**")
			assert language, await ctx.send(f"**Please, {author.mention}, inform the `language`!**")
			assert len(language) < 80, await ctx.send(f"**Please, {author.mention}, the `language` must be under 31 characters!**")
			assert weekday, await ctx.send(f"**Please, {author.mention}, inform the `weekday`!**")
			assert len(weekday) < 9, await ctx.send(f"**Please, {author.mention}, the `weekday` must be under 10 characters!**")
			assert time, await ctx.send(f"**Please, {author.mention}, inform the `time`!**")
			assert len(weekday) < 25, await ctx.send(f"**Please, {author.mention}, the `time` must be under 25 characters!**")
		except AssertionError as e:
			return

		# Card template path
		path = './media/templates/empty_template.png'

		# Teacher info
		teacher_name = teacher.name
		language = language.lower()
		description = await self.make_description(description)
		weekday = weekday.capitalize()
		time = time.upper()

		# Image info
		small = ImageFont.truetype('./media/fonts/Nougat-ExtraBlack.ttf', 28)

		# Opening images
		background = Image.open(path).resize((685, 485))
		template = Image.open('./media/templates/card_template.png').resize((685, 485))
		icon = await self.get_teacher_pfp(teacher)
		flag = Image.open(await self.get_flag(language)).resize((690, 490))

		# Pasting images
		background.paste(flag, (0, -2), flag)
		background.paste(icon, (438, 102), icon)
		background.paste(template, (0, 0), template)

		# Writing the text  (0 196, 187) | (5, 66, 39)
		draw = ImageDraw.Draw(background) 
		await self.paste_text(draw, (230, 100), teacher_name, (0, 196, 187), small, (5, 66, 39))
		await self.paste_text(draw, (230, 136), language.title(), (0, 196, 187), small, (5, 66, 39))
		await self.paste_text(draw, (230, 172), weekday, (0, 196, 187), small, (5, 66, 39))
		await self.paste_text(draw, (230, 208), time, (0, 196, 187), small, (5, 66, 39))
		await self.paste_text(draw, (170, 280), description, (0, 196, 187), small, (5, 66, 39))


		# Get current timestamp
		epoch = datetime.utcfromtimestamp(0)
		the_time = (datetime.utcnow() - epoch).total_seconds()

		# Saving the image
		saved_path = f'./media/temporary/card-{the_time}.png'
		background.save(saved_path, 'png', quality=90)
		await ctx.send(file=discord.File(saved_path))
		os.remove(saved_path)

	@commands.command(aliases=['epfp'])
	@commands.has_permissions(administrator=True)
	async def export_profile_picutres(self, ctx) -> None:
		""" Exports a zip file with all of the teachers' profile picture. """

		path = 'media/icons/'
		guild = ctx.guild
		# print(ctx.author.roles)
		teacher_role = discord.utils.get(guild.roles, id=self.teacher_role_id)
		# print(teacher_role)
		# print(teacher_role in ctx.author.roles)
		teachers = [m for m in guild.members if teacher_role in m.roles]
		teacher_names = []

		# Creates the icons folder
		try:
			os.makedirs(f'./media/icons/')
			os.makedirs(f'./media/temporary/')
		except FileExistsError:
			pass

		for teacher in teachers:
			pfp = await self.get_teacher_pfp(teacher)
			pfp.save(f"{path}{teacher.name}.png", 'png', quality=90)
			teacher_names.append(teacher.name)

		# Makes a temporary text file containing all teacher names
		with open('media/icons/teacher_names.txt', 'w+') as f:
			for name in teacher_names:
				f.write(f"{name}\n")

		# Compresses all files in the /icons folder and puts it into the temporary folder
		with ZipFile('media/temporary/teacher_icons.zip', 'w') as zip:
			for file in os.listdir(path):
				full_path = os.path.join(path, file)
				print(full_path)
				zip.write(full_path, file)



		await ctx.send(file=discord.File('media/temporary/teacher_icons.zip'))

		# Deletes the icons folder
		try:
			shutil.rmtree('./media/icons')
			shutil.rmtree('./media/temporary')
		except Exception as e:
			pass


	async def get_flag(self, language: str) -> str:
		""" Gets the flag for the given language if there is one, otherwise returns the default flag. 

		:param language: The language from which to get the flag.
		:returns: The flag path.
		"""

		# Gets and Converts the JSON that contains the flag paths to a dictionary
		with open('./media/flags/flags.json', 'r') as f:
			flags = json.load(f)

		# Loops through the dictionary searching for the flag
		for row in flags.values():
			for path, aliases in row.items():
				if language.lower() in aliases:
					return f"media/flags/{path}"
		# If not found, returns the default one
		else:
			return './media/flags/default.png'


	@commands.command(aliases=['uc'])
	@commands.has_permissions(administrator=True)
	async def update_classes(self, ctx):
		""" Update the teachers' classes, by requesting new cards from
		the server's website """

		async with ctx.typing():
			try:
				async with self.session.get(self.website_link) as response:
					data = json.loads(await response.read())
					
			except Exception as e:
				await ctx.send("**No!**")
			else:

				# Checks whether new cards were fetched from the website
				if not data:
					return await ctx.send("**No are available cards to update!**")

				# Clears the classes channel
				await self.clear_classes_channel(ctx.guild)
				sorted_weekdays = await self.sort_weekdays(data)
				channel = discord.utils.get(ctx.guild.channels, id=self.classes_channel_id)
				for day, classes in sorted_weekdays.items():
					print(f"{day=}")
					await channel.send(embed=discord.Embed(
						title=day,
						color=discord.Color.green()))
					for teacher_class in classes:
						msg = await channel.send(teacher_class)
						await msg.add_reaction('✅')
						await asyncio.sleep(0.5)


	async def clear_classes_channel(self, guild: discord.Guild) -> None:
		""" Clears all messages from the classes channel. """

		channel = discord.utils.get(guild.channels, id=self.classes_channel_id)
		while True:
			msgs = await channel.history().flatten()
			if (lenmsg := len(msgs)) > 0:
				await channel.purge(limit=lenmsg)
			else:
				break

	async def sort_weekdays(self, data: List[Dict[str, Union[int, str]]]) -> Dict[str, List[str]]:
		""" Sorts the given data by the days of the week. """

		weekdays: Dict[str, List[str]] = {
			'Sunday': [], 
			'Monday': [], 
			'Tuesday': [], 
			'Wednesday': [], 
			'Thursday': [], 
			'Friday': [], 
			'Saturday': [],
		}

		for teacher_class in data:
			weekdays[teacher_class['weekday']].append(teacher_class['image'])

		return weekdays


def setup(client) -> None:
	client.add_cog(TeacherAPI(client))