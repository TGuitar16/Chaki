import discord
from discord.ext import commands
import os
import random
import json

WORD_LIST_FILE = 'Chaki/word_list.csv'
RANKING_FILE = 'Chaki/rankings.json'

def load_rankings():
  if os.path.exists(RANKING_FILE):
    with open(RANKING_FILE, 'r') as f:
      return json.load(f)
  return {}

def save_rankings(rankings):
  with open(RANKING_FILE, 'w') as f:
    json.dump(rankings, f)

def load_word_list():
  with open(WORD_LIST_FILE, 'r', encoding='utf-8') as f:
    return [line.strip() for line in f.readlines()]

class WordChain(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.word_list = load_word_list()
    self.current_word = None
    self.players = {}
    self.rankings = load_rankings()
    self.active_games = {}

  @discord.app_commands.command(name="끝말잇기", description="끝말잇기를 시작합니다. (n인용)")
  async def 시작(self, interaction: discord.Interaction, num_players: int):
    if num_players < 1 or num_players > 5:
      await interaction.response.send_message("플레이어 수는 1명 이상, 5명 이하로 설정해야 합니다.")
      return

    server_id = str(interaction.guild.id)
    if server_id in self.active_games:
      await interaction.response.send_message("이미 진행 중인 끝말잇기 게임이 있습니다.")
      return

    self.current_word = random.choice(self.word_list)
    self.active_games[server_id] = {
      "current_word": self.current_word,
      "players": [],
      "turn_index": 0,
      "waiting_for_players": num_players > 1,
      "game_started": num_players == 1
    }

    if num_players == 1:
      self.active_games[server_id]["players"].append(interaction.user)  # 1인용 시 플레이어 추가
      await interaction.response.send_message(f"끝말잇기 1인용 게임을 시작합니다! 첫 단어: {self.current_word}")
      await self.start_game(server_id, interaction)
    else:
      await interaction.response.send_message(f"{num_players}인용 끝말잇기 게임이 준비되었습니다. 참가하려면 아래 버튼을 눌러주세요.", view=self.create_join_button(num_players))


  def create_join_button(self, num_players):
    view = discord.ui.View()
    join_button = discord.ui.Button(label="참가하기")
    leave_button = discord.ui.Button(label="나가기", style=discord.ButtonStyle.danger)

    async def join_callback(interaction: discord.Interaction):
      await interaction.response.defer(ephemeral=True)  # 응답 지연
      server_id = str(interaction.guild.id)
      game = self.active_games[server_id]

      if game["game_started"]:
        await interaction.followup.send("게임이 이미 시작되어 새로운 참가가 불가합니다.", ephemeral=True)
        return

      if interaction.user in game["players"]:
        await interaction.followup.send("이미 참가하셨습니다.", ephemeral=True)
        return

      game["players"].append(interaction.user)

      if len(game["players"]) >= num_players:
        game["waiting_for_players"] = False
        game["game_started"] = True
        await interaction.followup.send("모든 참가자가 등록되었습니다. 게임을 시작합니다!")
        await self.start_game(server_id, interaction)
      else:
        await interaction.followup.send(f"{interaction.user.mention}님이 참가했습니다! 현재 참가자: {len(game['players'])}/{num_players}")

    async def leave_callback(interaction: discord.Interaction):
      await interaction.response.defer(ephemeral=True)  # 응답 지연
      server_id = str(interaction.guild.id)
      game = self.active_games[server_id]

      if game["game_started"]:
        await interaction.followup.send("게임이 이미 시작되어 이탈할 수 없습니다.", ephemeral=True)
        return

      if interaction.user not in game["players"]:
        await interaction.followup.send("참가하지 않았습니다.", ephemeral=True)
        return

      game["players"].remove(interaction.user)

      if not game["players"]:
        await interaction.followup.send("모든 플레이어가 나갔습니다. 게임을 종료합니다.")
        del self.active_games[server_id]
      else:
        await interaction.followup.send(f"{interaction.user.mention}님이 게임에서 나갔습니다. 남은 참가자: {len(game['players'])}")

    join_button.callback = join_callback
    leave_button.callback = leave_callback
    view.add_item(join_button)
    view.add_item(leave_button)
    return view

  async def start_game(self, server_id, interaction):
    game = self.active_games[server_id]
    current_turn_player = game["players"][game["turn_index"]] if game["players"] else interaction.user

    await interaction.followup.send(
      f"끝말잇기가 시작되었습니다! 첫 단어: {self.current_word}\n{current_turn_player.mention}님의 차례입니다.",
      view=self.create_word_button(self.current_word))

  @discord.app_commands.command(name="단어", description="다음 단어를 입력합니다.")
  async def 단어(self, interaction: discord.Interaction, word: str):
    server_id = str(interaction.guild.id)
    if server_id not in self.active_games or self.active_games[server_id]["waiting_for_players"]:
      await interaction.response.send_message("현재 진행 중인 끝말잇기 게임이 없습니다.")
      return

    game = self.active_games[server_id]
    current_turn_player = game["players"][game["turn_index"]]

    if interaction.user != current_turn_player:
      await interaction.response.send_message(f"지금은 {current_turn_player.mention}님의 차례입니다.", ephemeral=True)
      return

    last_char = self.current_word[-1]
    if word[0] != last_char:
      await interaction.response.send_message(f"잘못된 단어입니다. {last_char}(으)로 시작하는 단어를 입력하세요.")
      return

    if word not in self.word_list:
      await interaction.response.send_message(f"{word}은(는) 단어 리스트에 없는 단어입니다. 다시 입력하세요.")
      return

    self.current_word = word
    game["turn_index"] = (game["turn_index"] + 1) % len(game["players"])  # 다음 참가자의 차례로 변경

    # 다음 차례에 사용할 수 있는 단어 확인
    available_words = [w for w in self.word_list if w[0] == self.current_word[-1]]
    if available_words:
      bot_word = random.choice(available_words)
      await interaction.response.send_message(f"{interaction.user.mention}님이 입력한 단어: {self.current_word}, 다음 단어는: {bot_word}입니다!")
      self.current_word = bot_word 
    else:
      # 가능한 단어가 없는 경우 자동 패배 처리
      await interaction.response.send_message(f"{interaction.user.mention}님이 {self.current_word}을(를) 입력해 승리했습니다! 봇이 선택할 단어가 없습니다.")
      self.update_score(interaction.user, 1, server_id)
      del self.active_games[server_id]
      return

    # 다인용일 때만 "다음 차례는" 메시지를 보냄
    if len(game["players"]) > 1:
      next_turn_player = game["players"][game["turn_index"]]

      # 다음 차례 사용자가 사용할 수 있는 단어가 있는지 확인
      next_available_words = [w for w in self.word_list if w[0] == self.current_word[-1]]
      if not next_available_words:
        # 사용 가능한 단어가 없다면 자동 패배 처리
        await interaction.followup.send(f"{next_turn_player.mention}님은 사용할 수 있는 단어가 없어 자동 패배하였습니다.")
        self.update_score(next_turn_player, -1, server_id)
        del self.active_games[server_id]
        return

      await interaction.followup.send(f"다음 차례는 {next_turn_player.mention}님의 차례입니다.")

  def update_score(self, user, score_change, server_id):
    user_id = str(user.id)
    if user_id not in self.rankings[server_id]:
      self.rankings[server_id][user_id] = 0
    self.rankings[server_id][user_id] += score_change
    save_rankings(self.rankings)

  @discord.app_commands.command(name="포기", description="끝말잇기를 포기합니다.")
  async def 포기(self, interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    if server_id not in self.active_games:
      await interaction.response.send_message("현재 진행 중인 끝말잇기 게임이 없습니다.")
      return

    user_id = str(interaction.user.id)
    if user_id not in self.rankings[server_id]:
      self.rankings[server_id][user_id] = 0  # 초기 점수 설정

    self.rankings[server_id][user_id] -= 1  # 점수 -1 부여
    await interaction.response.send_message(f"{interaction.user.mention}님이 끝말잇기를 포기했습니다. 점수 -1 부여!")

    save_rankings(self.rankings)
    del self.active_games[server_id]

  @discord.app_commands.command(name="끝말잇기_랭킹", description="끝말잇기 랭킹을 확인합니다.")
  async def 랭킹(self, interaction: discord.Interaction):
    server_id = str(interaction.guild.id)
    rankings = self.rankings.get(server_id, {})

    if not rankings:
      await interaction.response.send_message("현재 랭킹이 없습니다.")
      return

    ranking_list = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
    response = "현재 끝말잇기 랭킹:\n" + "\n".join([f"<@{user_id}>: {score}점" for user_id, score in ranking_list])
    await interaction.response.send_message(response)

  def create_word_button(self, word):
    button = discord.ui.Button(label="무슨 단어지?", url=f"https://search.naver.com/search.naver?query={word}")
    view = discord.ui.View()
    view.add_item(button)
    return view
  
  @discord.app_commands.command(name="점수", description="특정 사용자의 점수를 확인합니다.")
  async def 점수(self, interaction: discord.Interaction, user: discord.User = None):
    server_id = str(interaction.guild.id)
    if not user:
      user = interaction.user
    user_id = str(user.id)
    score = self.rankings.get(server_id, {}).get(user_id, 0)
    await interaction.response.send_message(f"{user.mention}님의 점수는 {score}점입니다.")

  @discord.app_commands.command(name="점수변경", description="특정 사용자의 끝말잇기 점수를 변경합니다. (관리자 전용)")
  @commands.has_permissions(administrator=True)
  async def change_score(self, interaction: discord.Interaction, user: discord.User, new_score: int):
    server_id = str(interaction.guild.id)
    user_id = str(user.id)

    if server_id not in self.rankings:
      self.rankings[server_id] = {}

    self.rankings[server_id][user_id] = new_score  # 점수 변경
    save_rankings(self.rankings)

    await interaction.response.send_message(f"{user.mention}님의 점수가 {new_score}점으로 변경되었습니다.")

  # 권한 부족 시 에러 메시지 처리
  @change_score.error
  async def change_score_error(self, interaction: discord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
      await interaction.response.send_message("이 명령어를 실행하려면 관리자 권한이 필요합니다.", ephemeral=True)

async def setup(bot):
  await bot.add_cog(WordChain(bot))
