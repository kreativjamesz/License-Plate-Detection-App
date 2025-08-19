# 🔄 Development State Caching Example

## How it works:

### Before (walang state caching):
1. You're working on the Students page
2. You edit some code
3. Hot reload triggers
4. App restarts and goes back to Home page
5. You have to navigate back to Students page manually 😞

### After (with state caching):
1. You're working on the Students page
2. You edit some code
3. Hot reload triggers
4. App restarts and **automatically goes back to Students page** 🎉
5. Your login session is preserved too!

## Usage:

```bash
# Start development with state caching
python dev.py
```

## Features:

- ✅ **Page Persistence** - Remembers kung anong page ka nandoon
- ✅ **Login Session** - Remembers kung logged in ka at sino yung user
- ✅ **Route Memory** - Even dashboard/students/attendance routes
- ✅ **Auto Cleanup** - Removes state file when dev server stops
- ✅ **Production Safe** - Only works in dev mode, hindi sa production

## Example State File (.dev_state.json):

```json
{
  "current_user": "admin",
  "current_route": "students",
  "timestamp": "/path/to/project"
}
```

## Dev vs Production:

| Mode | State Caching | Behavior |
|------|---------------|----------|
| Development (`python dev.py`) | ✅ Enabled | Restores last page |
| Production (`python main.py`) | ❌ Disabled | Always starts at home |

## Technical Details:

1. **State Detection**: Uses `DEV_MODE=true` environment variable
2. **State Storage**: JSON file `.dev_state.json` (gitignored)
3. **State Saving**: On every navigation change + app exit
4. **State Restoration**: On app startup in dev mode
5. **Cleanup**: Automatic removal on dev server stop
