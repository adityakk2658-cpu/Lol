# Lolgram

An Instagram-style photo-sharing web app built with plain HTML, CSS and JavaScript — no build step, no dependencies.

## Run it

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Features

- **Feed** with posts from accounts you follow, then "suggested posts"
- **Like** (button or double-tap the photo), **save**, **comment**, reply, like/delete comments, copy link
- **Stories** bar with a full-screen viewer: progress bars, auto-advance, tap/arrow-key navigation, hold to pause, reply box
- **Post detail** modal with the full comment thread
- **Create post**: upload or drag-and-drop a photo (or pick a random one), add a caption with `#tags` / `@mentions`, location and filters
- **Profiles** with post grid, saved tab, follower/following lists, follow/unfollow, edit profile (name, bio, photo)
- **Explore** grid ranked by engagement, plus hashtag pages (`#/explore?tag=travel`)
- **Search** panel for users and hashtags; **Notifications** panel
- **Light / dark mode**, responsive layout (desktop sidebar → icon rail → mobile top + bottom bars)
- Everything persists in `localStorage`; "Reset demo data" in the sidebar footer restores the seed data

## Files

| File | Purpose |
| --- | --- |
| `index.html` | App shell and navigation |
| `style.css` | All styling, themes and responsive breakpoints |
| `data.js` | Fictional seed users, posts, stories and notifications |
| `app.js` | Router, rendering, state and interactions |

Sample photos come from [picsum.photos](https://picsum.photos); if they can't load, a gradient placeholder is shown.
