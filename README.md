# kokobot
An amazing, awesome, super cool Discord bot UT Austin SASE.

## TODO
### Easy (discord.py, Python)
- Koko: Sanitize string input to have a maximum length.
- Koko: Allow for note chaining up to some number of notes (30 maybe?). BUT, avoid recursion.

### Medium (discord.py, Python, implementation stuff)
- Koko: `$koko modify` instead `$koko remove` first then `$koko add`.
- Add emoji create, delete, list, and search.

### Hard (discord.py, Python, sqlite3, ask me for Amazon credentials stuff)
- Custom emoji used counter in database for all messages. Need to include date added, and probably store emoji based on emoji id if there is (check discord.py API)?
- On custom emoji add, remove, or update, do database update.
- Add kokobot command counters in database.

### Very Hard (discord.py, Python, sqlite3, Amazon S3 APIs, ask me for Amazon credentials stuff)
- Use S3 API to save uploaded pics and files for notes (maximum file size to be 10 Mb?), and store their links into database.

## TODO (Low-Priority)
### Easy (Python)
- Fix Python packaging so that kokobot is a legit project and module.
