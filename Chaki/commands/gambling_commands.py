import discord
from discord.ext import commands
from datetime import datetime, timedelta
import os
import json
import random

# CommandSetUp
class OddEvenGameView(discord.ui.View):
  def __init__(self, bet_amount, selected_choice, original_user):
    super().__init__(timeout=30)
    self.bet_amount = bet_amount
    self.selected_choice = selected_choice
    self.original_user = original_user  # 명령어를 실행한 사용자를 저장
    self.result = None

  @discord.ui.button(label="⚫ 홀", style=discord.ButtonStyle.secondary)
  async def 홀(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.process_selection(interaction, "홀")

  @discord.ui.button(label="⚪ 짝", style=discord.ButtonStyle.primary)
  async def 짝(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.process_selection(interaction, "짝")

  async def process_selection(self, interaction, choice):
    if interaction.user == self.original_user:
      await interaction.response.send_message("본인이 선택한 것을 맞출 수 없습니다!", ephemeral=True)  # 선택자가 자신 것을 고르는 것을 방지
      return

    if choice == self.selected_choice:
      await interaction.response.send_message(f"🎉 {interaction.user.mention}님이 '{self.selected_choice}'을(를) 맞췄습니다!", ephemeral=False)
    else:
      await interaction.response.send_message(f"😢 {interaction.user.mention}님이 '{self.selected_choice}'을(를) 맞추지 못했습니다.", ephemeral=False)
    self.stop()

class OddEvenSelectionView(discord.ui.View):
  def __init__(self, interaction, bet_amount):
    super().__init__(timeout=30)
    self.interaction = interaction
    self.bet_amount = bet_amount
    self.result = None

  @discord.ui.button(label="⚫ 홀", style=discord.ButtonStyle.secondary)
  async def 홀(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.process_selection(interaction, "홀")

  @discord.ui.button(label="⚪ 짝", style=discord.ButtonStyle.primary)
  async def 짝(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self.process_selection(interaction, "짝")

  async def process_selection(self, interaction, choice):
    if interaction.user != self.interaction.user:
      await interaction.response.send_message("이 버튼은 당신을 위한 것이 아닙니다.", ephemeral=True)
      return

    self.result = choice
    await interaction.response.send_message(f"{self.interaction.user.mention}님이 '{choice}'을(를) 선택했습니다.", ephemeral=True)
    self.stop()

# Commands
class GamblingCommands(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.money_file = "Chaki/ownmoney.json"

    if not os.path.exists(self.money_file):
      with open(self.money_file, 'w') as f:
        json.dump({}, f)

  @discord.app_commands.command(name="돈줘", description="도박에 필요한 돈을 받습니다.")
  async def 돈줘(self, interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    with open(self.money_file, 'r') as f:
      data = json.load(f)

    if server_id not in data:
      data[server_id] = {}

    server_data = data[server_id]
    user_data = server_data.get(user_id, {"money": 0, "last_received": None})
    
    last_received_str = user_data.get("last_received")
    if last_received_str:
      last_received = datetime.fromisoformat(last_received_str)
      if datetime.now() - last_received < timedelta(days=1):
        await interaction.response.send_message(f"{interaction.user.mention}, 마지막으로 돈을 받은 지 24시간이 지나지 않았습니다. 마지막 수령: {last_received}")
        return

    user_data["money"] += 10000
    user_data["last_received"] = datetime.now().isoformat()

    server_data[user_id] = user_data
    data[server_id] = server_data

    with open(self.money_file, 'w') as f:
      json.dump(data, f)

    await interaction.response.send_message(f"{interaction.user.mention}, 10,000원을 받았습니다. 현재 잔액: {user_data['money']:,}원")

  @discord.app_commands.command(name="도박", description="도박을 합니다.")
  async def 도박(self, interaction: discord.Interaction, 금액: int, 배수: int):
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if 금액 <= 0 or 배수 < 1 or 배수 > 10:
      await interaction.response.send_message(f"{interaction.user.mention}, 양수의 금액과 1에서 10 사이의 배수를 입력해주세요.")
      return

    with open(self.money_file, 'r') as f:
      data = json.load(f)

    if server_id not in data:
      data[server_id] = {}

    server_data = data[server_id]
    user_data = server_data.get(user_id, {"money": 0})

    if user_data["money"] <= 0:
      await interaction.response.send_message(f"{interaction.user.mention}, 잔액이 없습니다.")
      return

    if user_data["money"] < 금액:
      await interaction.response.send_message(f"{interaction.user.mention}, 보유 금액이 부족합니다. 현재 잔액: {user_data['money']:,}원")
      return

    total_bet = 금액 * 배수
    success_rate = random.uniform(0.01, 99.9)

    if random.uniform(0, 100) < success_rate:
      user_data["money"] += total_bet
      result_message = f"🎉 성공! 잔액: {user_data['money']:,}원 (확률: {success_rate:.2f}%)"
    else:
      user_data["money"] -= 금액
      result_message = f"😢 실패! 잔액: {user_data['money']:,}원 (확률: {success_rate:.2f}%)"

    server_data[user_id] = user_data
    data[server_id] = server_data

    with open(self.money_file, 'w') as f:
      json.dump(data, f)

    await interaction.response.send_message(result_message)

  @discord.app_commands.command(name="잔액", description="본인의 잔액을 확인합니다.")
  async def 잔액(self, interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    with open(self.money_file, 'r') as f:
      data = json.load(f)

    server_data = data.get(server_id, {})
    user_data = server_data.get(user_id, {"money": 0})

    await interaction.response.send_message(f"{interaction.user.mention}, 현재 잔액: {user_data['money']:,}원")

  @discord.app_commands.command(name="도박랭킹", description="서버의 잔액 랭킹을 확인합니다.")
  async def 도박랭킹(self, interaction: discord.Interaction, 유저: discord.Member = None):
    server_id = str(interaction.guild.id)

    with open(self.money_file, 'r') as f:
      data = json.load(f)

    server_data = data.get(server_id, {})
    rankings = sorted(server_data.items(), key=lambda x: x[1]['money'], reverse=True)

    if 유저 is not None:
      user_id = str(유저.id)
      user_money = server_data.get(user_id, {"money": 0})["money"]
      user_rank = next((index + 1 for index, (uid, info) in enumerate(rankings) if uid == user_id), None)
      if user_rank is not None:
        await interaction.response.send_message(f"{유저.mention}의 잔액: {user_money:,}원, 랭킹: {user_rank}위")
      else:
        await interaction.response.send_message(f"{유저.mention}은 이 서버에 잔액이 없습니다.")
    else:
      if not rankings:
        await interaction.response.send_message("서버에 잔액이 있는 유저가 없습니다.")
        return

      ranking_message = "서버 잔액 랭킹:\n"
      for rank, (uid, info) in enumerate(rankings, start=1):
        ranking_message += f"{rank}위: <@{uid}> - 잔액: {info['money']:,}원\n"
      
      await interaction.response.send_message(ranking_message)
    
  @discord.app_commands.command(name="잔액조정", description="유저의 잔액을 조정합니다.")
  @discord.app_commands.checks.has_permissions(administrator=True)
  async def 잔액조정(self, interaction: discord.Interaction, 유저: discord.User, 변경금액: int):
    server_id = str(interaction.guild.id)
    user_id = str(유저.id)

    with open(self.money_file, 'r') as f:
      data = json.load(f)

    if server_id not in data:
      data[server_id] = {}

    server_data = data[server_id]
    user_data = server_data.get(user_id, {"money": 0})
    
    user_data["money"] += 변경금액
    server_data[user_id] = user_data
    data[server_id] = server_data

    with open(self.money_file, 'w') as f:
      json.dump(data, f)

    await interaction.response.send_message(f"{interaction.user.mention}님이 {유저.mention}의 잔액을 {변경금액:,}원 조정했습니다. 새로운 잔액: {user_data['money']:,}원")

  @discord.app_commands.command(name="홀짝", description="2인용 홀짝 게임을 합니다.")
  async def 홀짝(self, interaction: discord.Interaction, 금액: int):
    if 금액 <= 0:
      await interaction.response.send_message(f"{interaction.user.mention}, 양수의 금액을 입력해주세요.")
      return

    selection_view = OddEvenSelectionView(interaction, 금액)
    await interaction.response.send_message(f"{interaction.user.mention}, 홀 또는 짝을 선택해주세요!", view=selection_view, ephemeral=True)

    await selection_view.wait()

    if selection_view.result is None:
      await interaction.followup.send(f"{interaction.user.mention}, 시간이 초과되었습니다.", ephemeral=True)
      return

    selected_choice = selection_view.result
    await interaction.followup.send(f"@everyone {interaction.user.mention}님이 선택한 걸 맞춰보세요!", ephemeral=False)

    guess_view = OddEvenGameView(bet_amount=금액, selected_choice=selected_choice, original_user=interaction.user)
    await interaction.followup.send("홀짝을 맞춰보세요!", view=guess_view, ephemeral=False)

async def setup(bot):
  await bot.add_cog(GamblingCommands(bot))