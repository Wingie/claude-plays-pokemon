19June user Testing Notes:
--------------------------
- we need a way to note and explain direction to the bot (like viridian forest is north of viridian city) as he is just walking randomly now
- logging things to the terminal should be informative to the user for debugging (because i saw this on the screen i am going to press this sequence "" )
- basically there are things in the screen that gemini sees, and there are things outside the screen
- we can be in the overworld, a room, gyms or other maxes like mt moon. each place should have a playbook.
- so when travelling, a navigation playubook with lots of information learnt about travelling in the game\
- and when battloing, the data is stored in a battle playbook eg navigation.md, battling.md, brock_gym.md etc
- this shoukd allow the system to get notes (eg: if in viridian city, which direction should be travel to get to viridian forest)
- also during battles, its not able to get the menus or use potions, its not very smart (maybe it doesnt see the menu select icon?)

GOAL: - a common pattern in the game would be to remember where you are, go to the nearest pokecenterm heal your pokemion and come back to where you are. this is what im trying to see if we can do this but WITHOUT explicitly coding it in the prompts.