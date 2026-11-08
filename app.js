/* Lolgram — a single-page photo-sharing app. No build step, no dependencies. */
(function () {
  "use strict";

  /* ================= icons ================= */
  const P = (d, extra = "") =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ${extra}>${d}</svg>`;
  const ICONS = {
    home: P('<path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>'),
    search: P('<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>'),
    explore: P('<circle cx="12" cy="12" r="10"/><path d="m16 8-2.5 5.5L8 16l2.5-5.5z"/>'),
    heart: P('<path d="M12 21s-7.5-4.6-9.5-9.3C1.1 8.3 3.3 4.5 7 4.5c2.1 0 3.6 1.1 5 3 1.4-1.9 2.9-3 5-3 3.7 0 5.9 3.8 4.5 7.2C19.5 16.4 12 21 12 21z"/>'),
    plus: P('<rect x="3" y="3" width="18" height="18" rx="5"/><path d="M12 8v8M8 12h8"/>'),
    moon: P('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>'),
    sun: P('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    comment: P('<path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20.5l1.6-5A8.5 8.5 0 1 1 21 11.5z"/>'),
    share: P('<path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/>'),
    bookmark: P('<path d="M19 21 12 16 5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1z"/>'),
    more: P('<circle cx="5" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="19" cy="12" r="1.3" fill="currentColor"/>'),
    close: P('<path d="M18 6 6 18M6 6l12 12"/>'),
    grid: P('<rect x="3" y="3" width="18" height="18"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/>'),
    gallery: P('<rect x="2" y="5" width="16" height="14" rx="2"/><path d="M22 8v12a1 1 0 0 1-1 1H6"/><circle cx="7.5" cy="10" r="1.5"/><path d="m18 15-4-4-8 8"/>', 'stroke-width="1.4"'),
    back: P('<path d="M15 18 9 12l6-6"/>'),
    settings: P('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
    verified: '<svg viewBox="0 0 24 24"><path fill="currentColor" d="m12 1 2.6 2 3.3-.2.9 3.2 2.8 1.8-1.2 3.2 1.2 3.2-2.8 1.8-.9 3.2-3.3-.2L12 23l-2.6-2-3.3.2-.9-3.2-2.8-1.8L3.6 13 2.4 9.8l2.8-1.8.9-3.2 3.3.2z"/><path d="m8 12 3 3 5-6" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  };
  const icon = (name, cls = "") => `<span class="ico ${cls}">${ICONS[name] || ""}</span>`;
  function hydrateIcons(root = document) {
    root.querySelectorAll("[data-icon]").forEach((el) => {
      if (!el.dataset.hydrated) { el.innerHTML = ICONS[el.dataset.icon] || ""; el.dataset.hydrated = "1"; }
    });
  }

  /* ================= state ================= */
  const KEY = "lolgram:v1";
  let state;
  function load() {
    try { state = JSON.parse(localStorage.getItem(KEY)); } catch (_) { state = null; }
    if (!state || !state.users || !state.posts) {
      state = JSON.parse(JSON.stringify(window.SEED));
      state.theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); }
    catch (_) { toast("Storage is full — large photos may not persist."); }
  }

  const userBy = (u) => state.users.find((x) => x.username === u);
  const postBy = (id) => state.posts.find((p) => p.id === id);
  const me = () => userBy("me");
  const isFollowing = (u) => state.following.includes(u);

  /* ================= helpers ================= */
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmtNum = (n) => n >= 1e6 ? (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M" : n >= 1e4 ? (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K" : n.toLocaleString();
  function ago(t, long = false) {
    const s = Math.max(1, Math.floor((Date.now() - t) / 1000));
    const units = [["y", 31536000, "year"], ["w", 604800, "week"], ["d", 86400, "day"], ["h", 3600, "hour"], ["m", 60, "minute"], ["s", 1, "second"]];
    for (const [abbr, sec, word] of units) {
      const v = Math.floor(s / sec);
      if (v >= 1) return long ? `${v} ${word}${v > 1 ? "s" : ""} ago` : `${v}${abbr}`;
    }
  }
  function richText(text) {
    return esc(text)
      .replace(/#(\w+)/g, '<a class="tag" href="#/explore?tag=$1">#$1</a>')
      .replace(/@([\w.]+)/g, (m, u) => userBy(u) ? `<a class="tag" href="#/profile/${u}">@${u}</a>` : m);
  }
  const verified = (u) => (u && u.verified ? `<span class="verified" title="Verified">${ICONS.verified}</span>` : "");
  const FALLBACK = "data:image/svg+xml;utf8," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f9ce34"/><stop offset=".5" stop-color="#ee2a7b"/><stop offset="1" stop-color="#6228d7"/></linearGradient></defs><rect width="10" height="10" fill="url(#g)"/></svg>');
  document.addEventListener("error", (e) => {
    if (e.target.tagName === "IMG" && e.target.src !== FALLBACK) e.target.src = FALLBACK;
  }, true);
  const uid = () => Math.random().toString(36).slice(2, 10);

  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2400);
  }

  /* ================= theme ================= */
  function applyTheme() {
    document.documentElement.dataset.theme = state.theme;
    document.querySelectorAll('[data-action="theme"] .ico').forEach((el) => {
      el.innerHTML = ICONS[state.theme === "dark" ? "sun" : "moon"];
    });
  }

  /* ================= rendering: pieces ================= */
  function avatarLink(username, size = "sm", withRing = false) {
    const u = userBy(username);
    const img = `<img class="avatar ${size}" src="${esc(u?.avatar)}" alt="${esc(username)}'s profile picture" loading="lazy" />`;
    if (!withRing) return `<a href="#/profile/${esc(username)}">${img}</a>`;
    const st = state.stories.find((s) => s.user === username);
    if (!st) return `<a href="#/profile/${esc(username)}">${img}</a>`;
    return `<button class="ring ${st.seen ? "seen" : ""}" data-action="story" data-user="${esc(username)}" aria-label="View ${esc(username)}'s story">${img}</button>`;
  }

  function postCard(p) {
    const u = userBy(p.user);
    const firstComments = p.comments.slice(-2);
    return `
    <article class="post" data-post="${p.id}">
      <div class="post-head">
        ${avatarLink(p.user, "sm", true)}
        <div class="who">
          <a href="#/profile/${esc(p.user)}">${esc(p.user)}</a>${verified(u)} <span class="muted">• ${ago(p.time)}</span>
          ${p.location ? `<div class="loc">${esc(p.location)}</div>` : ""}
        </div>
        <button data-action="post-menu" data-id="${p.id}" aria-label="More options">${icon("more")}</button>
      </div>
      <div class="post-media" data-action="dbl-like" data-id="${p.id}">
        <img src="${esc(p.image)}" alt="Photo by ${esc(p.user)}" loading="lazy" style="${p.filter ? `filter:${esc(p.filter)}` : ""}" />
        <span class="big-heart">${ICONS.heart.replace('fill="none"', 'fill="currentColor"')}</span>
      </div>
      <div class="post-body">
        ${actionsBar(p)}
        <button class="likes" data-action="likes-list" data-id="${p.id}">${fmtNum(p.likes)} likes</button>
        ${p.caption ? `<p class="caption"><a class="user" href="#/profile/${esc(p.user)}">${esc(p.user)}</a>${richText(p.caption)}</p>` : ""}
        ${p.comments.length > 2 ? `<button class="view-comments" data-action="open-post" data-id="${p.id}">View all ${p.comments.length} comments</button>` : ""}
        ${firstComments.map((c) => `<p class="caption comment-line"><a class="user" href="#/profile/${esc(c.user)}">${esc(c.user)}</a>${richText(c.text)}</p>`).join("")}
        <form class="add-comment" data-action="comment" data-id="${p.id}">
          <input name="text" placeholder="Add a comment…" autocomplete="off" aria-label="Add a comment" />
          <button type="submit" disabled>Post</button>
        </form>
      </div>
    </article>`;
  }

  function actionsBar(p) {
    return `
      <div class="actions">
        <button data-action="like" data-id="${p.id}" class="${p.liked ? "liked" : ""}" aria-label="${p.liked ? "Unlike" : "Like"}" aria-pressed="${p.liked}">${icon("heart")}</button>
        <button data-action="open-post" data-id="${p.id}" aria-label="Comment">${icon("comment")}</button>
        <button data-action="share" data-id="${p.id}" aria-label="Share">${icon("share")}</button>
        <span class="spacer"></span>
        <button data-action="save" data-id="${p.id}" class="${p.saved ? "saved" : ""}" aria-label="${p.saved ? "Remove from saved" : "Save"}" aria-pressed="${p.saved}">${icon("bookmark")}</button>
      </div>`;
  }

  function followBtn(username, cls = "btn primary") {
    if (username === "me") return "";
    const f = isFollowing(username);
    return `<button class="${f ? "btn" : cls}" data-action="follow" data-user="${esc(username)}">${f ? "Following" : "Follow"}</button>`;
  }

  function tile(p) {
    return `
      <button class="tile" data-action="open-post" data-id="${p.id}" aria-label="Open post by ${esc(p.user)}">
        <img src="${esc(p.image)}" alt="" loading="lazy" style="${p.filter ? `filter:${esc(p.filter)}` : ""}" />
        <span class="hover">
          <span>${ICONS.heart.replace('fill="none"', "")} ${fmtNum(p.likes)}</span>
          <span>${ICONS.comment.replace('fill="none"', "")} ${p.comments.length}</span>
        </span>
      </button>`;
  }

  /* ================= pages ================= */
  function renderHome() {
    const feedPosts = state.posts
      .filter((p) => p.user === "me" || isFollowing(p.user))
      .sort((a, b) => b.time - a.time);
    const others = state.posts.filter((p) => !feedPosts.includes(p)).sort((a, b) => b.time - a.time);
    const storyList = [...state.stories].sort((a, b) => a.seen - b.seen);
    const suggestions = state.users.filter((u) => u.username !== "me" && !isFollowing(u.username)).slice(0, 5);
    const m = me();

    return `
    <div class="home">
      <section class="feed">
        <div class="stories" role="list">
          ${storyList.map((s) => `
            <div class="story" role="listitem">
              <button class="ring ${s.seen ? "seen" : ""}" data-action="story" data-user="${esc(s.user)}" aria-label="View ${esc(s.user)}'s story">
                <img class="avatar" src="${esc(userBy(s.user)?.avatar)}" alt="" />
              </button>
              <span>${esc(s.user)}</span>
            </div>`).join("")}
        </div>
        ${feedPosts.map(postCard).join("")}
        ${others.length ? `
          <div class="empty" style="padding:24px 0 12px">
            <p class="bold" style="color:var(--text)">You're all caught up</p>
            <p>Suggested posts</p>
          </div>
          ${others.map(postCard).join("")}` : ""}
      </section>
      <aside class="rail">
        <div class="me-row">
          <a href="#/profile/me"><img class="avatar md" src="${esc(m.avatar)}" alt="" /></a>
          <div class="who"><a href="#/profile/me">${esc(m.username)}</a><small>${esc(m.name)}</small></div>
          <button class="link-btn" data-action="edit-profile">Edit</button>
        </div>
        ${suggestions.length ? `
          <div class="rail-head"><span>Suggested for you</span><a class="link-btn" style="color:var(--text)" href="#/explore">See all</a></div>
          ${suggestions.map((u) => `
            <div class="sugg">
              ${avatarLink(u.username, "sm")}
              <div class="who"><a href="#/profile/${esc(u.username)}">${esc(u.username)}</a>${verified(u)}<small>${fmtNum(u.followers)} followers</small></div>
              <button class="link-btn" data-action="follow" data-user="${esc(u.username)}">Follow</button>
            </div>`).join("")}` : ""}
        <div class="footer-links">
          About · Help · Privacy · Terms · Locations · Language<br />
          <span style="text-transform:uppercase">© 2026 Lolgram — a demo project</span><br />
          <button class="link-btn" data-action="reset">Reset demo data</button>
        </div>
      </aside>
    </div>`;
  }

  let profileTab = "posts";
  function renderProfile(username) {
    const u = userBy(username);
    if (!u) return `<div class="empty"><h2>Sorry, this page isn't available.</h2><p>The link may be broken. <a class="tag" href="#/">Go back home.</a></p></div>`;
    const own = username === "me";
    const posts = state.posts.filter((p) => p.user === username).sort((a, b) => b.time - a.time);
    const saved = state.posts.filter((p) => p.saved);
    const followers = u.followers + (isFollowing(username) ? 1 : 0);
    const following = own ? state.following.length : u.following;
    const list = own && profileTab === "saved" ? saved : posts;

    return `
    <div class="profile">
      <header class="profile-head">
        <div class="avatar-wrap">${(() => {
          const st = state.stories.find((s) => s.user === username);
          const img = `<img class="avatar xl" src="${esc(u.avatar)}" alt="${esc(u.username)}'s profile picture" />`;
          return st ? `<button class="ring ${st.seen ? "seen" : ""}" data-action="story" data-user="${esc(username)}">${img}</button>` : img;
        })()}</div>
        <div class="profile-info">
          <div class="profile-row">
            <h1>${esc(u.username)}${verified(u)}</h1>
            ${own
              ? `<button class="btn" data-action="edit-profile">Edit profile</button><button class="btn" data-action="create">New post</button>`
              : `${followBtn(username)}<button class="btn" data-action="message" data-user="${esc(username)}">Message</button>`}
          </div>
          <ul class="counts">
            <li><b>${posts.length}</b> posts</li>
            <li><button data-action="followers" data-user="${esc(username)}"><b>${fmtNum(followers)}</b> followers</button></li>
            <li><button data-action="following" data-user="${esc(username)}"><b>${fmtNum(following)}</b> following</button></li>
          </ul>
          <div class="profile-name">${esc(u.name)}</div>
          <p class="profile-bio">${richText(u.bio)}</p>
        </div>
      </header>
      <div class="tabs" role="tablist">
        <button class="${profileTab === "posts" || !own ? "active" : ""}" data-action="tab" data-tab="posts" role="tab">${icon("grid")} Posts</button>
        ${own ? `<button class="${profileTab === "saved" ? "active" : ""}" data-action="tab" data-tab="saved" role="tab">${icon("bookmark")} Saved</button>` : ""}
      </div>
      ${list.length
        ? `<div class="grid">${list.map(tile).join("")}</div>`
        : `<div class="empty">${icon(profileTab === "saved" && own ? "bookmark" : "gallery")}<h2>${own && profileTab === "saved" ? "Save" : own ? "Share photos" : "No posts yet"}</h2>
           <p>${own && profileTab === "saved" ? "Save photos you want to see again." : own ? "When you share photos, they will appear on your profile." : ""}</p>
           ${own && profileTab !== "saved" ? `<button class="btn primary" data-action="create">Share your first photo</button>` : ""}</div>`}
    </div>`;
  }

  function renderExplore(tag) {
    let posts = [...state.posts].sort((a, b) => (b.likes + b.comments.length * 50) - (a.likes + a.comments.length * 50));
    if (tag) posts = posts.filter((p) => new RegExp(`#${tag}\\b`, "i").test(p.caption));
    return `
    <div class="explore">
      ${tag ? `<div class="profile-row" style="padding:12px 16px"><h1 style="font-size:24px;margin:0">#${esc(tag)}</h1><span class="muted">${posts.length} posts</span><a class="btn" href="#/explore">Clear</a></div>` : ""}
      ${posts.length ? `<div class="grid">${posts.map((p, i) => tile(p).replace('class="tile"', `class="tile${!tag && i % 10 === 2 ? " big" : ""}"`)).join("")}</div>`
        : `<div class="empty"><h2>No posts</h2><p>Nothing tagged #${esc(tag)} yet.</p></div>`}
    </div>`;
  }

  /* ================= router ================= */
  function route() {
    closePanel();
    const hash = location.hash.replace(/^#/, "") || "/";
    const [path, query] = hash.split("?");
    const params = new URLSearchParams(query || "");
    const parts = path.split("/").filter(Boolean);
    const app = $("#app");
    let nav = "home";

    if (parts[0] === "explore") { app.innerHTML = renderExplore(params.get("tag")); nav = "explore"; }
    else if (parts[0] === "profile") {
      const u = decodeURIComponent(parts[1] || "me");
      if (app.dataset.profile !== u) profileTab = "posts";
      app.dataset.profile = u;
      app.innerHTML = renderProfile(u);
      nav = u === "me" ? "profile" : "";
    }
    else if (parts[0] === "p" && parts[1]) { app.innerHTML = renderHome(); openPost(parts[1]); }
    else app.innerHTML = renderHome();

    if (parts[0] !== "profile") delete app.dataset.profile;
    document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === nav));
    document.querySelectorAll("[data-me-avatar]").forEach((img) => (img.src = me().avatar));
    document.title = parts[0] === "profile" ? `${userBy(decodeURIComponent(parts[1] || "me"))?.name || "Profile"} • Lolgram` : parts[0] === "explore" ? "Explore • Lolgram" : "Lolgram";
  }
  // Re-render current view without losing scroll position
  function refresh() {
    const y = scrollY;
    const openId = $("#modal").dataset.post;
    const hash = location.hash.replace(/^#/, "") || "/";
    const [path, query] = hash.split("?");
    const parts = path.split("/").filter(Boolean);
    const app = $("#app");
    if (parts[0] === "explore") app.innerHTML = renderExplore(new URLSearchParams(query || "").get("tag"));
    else if (parts[0] === "profile") app.innerHTML = renderProfile(decodeURIComponent(parts[1] || "me"));
    else app.innerHTML = renderHome();
    document.querySelectorAll("[data-me-avatar]").forEach((img) => (img.src = me().avatar));
    scrollTo(0, y);
    if (openId && postBy(openId)) renderPostModal(openId);
  }

  /* ================= modal ================= */
  let lastFocus = null;
  function openModal(html, opts = {}) {
    const m = $("#modal");
    lastFocus = document.activeElement;
    m.innerHTML = `<button class="modal-close" data-action="close-modal" aria-label="Close">${icon("close")}</button>${html}`;
    m.hidden = false;
    m.dataset.kind = opts.kind || "";
    delete m.dataset.post;
    document.body.style.overflow = "hidden";
    const f = m.querySelector("[autofocus]") || m.querySelector(".dialog, .story-viewer");
    if (f) { f.setAttribute("tabindex", f.getAttribute("tabindex") || "-1"); f.focus(); }
  }
  function closeModal() {
    const m = $("#modal");
    if (m.hidden) return;
    stopStory();
    m.hidden = true;
    m.innerHTML = "";
    delete m.dataset.post;
    document.body.style.overflow = "";
    if (location.hash.startsWith("#/p/")) history.replaceState(null, "", "#/");
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  function renderPostModal(id) {
    const p = postBy(id);
    const u = userBy(p.user);
    const m = $("#modal");
    const html = `
      <div class="dialog detail" role="dialog" aria-label="Post by ${esc(p.user)}">
        <div class="media" data-action="dbl-like" data-id="${p.id}">
          <img src="${esc(p.image)}" alt="Photo by ${esc(p.user)}" style="${p.filter ? `filter:${esc(p.filter)}` : ""}" />
          <span class="big-heart">${ICONS.heart.replace('fill="none"', 'fill="currentColor"')}</span>
        </div>
        <div class="side">
          <div class="post-head">
            ${avatarLink(p.user, "sm", true)}
            <div class="who"><a href="#/profile/${esc(p.user)}">${esc(p.user)}</a>${verified(u)}
              ${p.user !== "me" && !isFollowing(p.user) ? ` • <button class="link-btn" data-action="follow" data-user="${esc(p.user)}">Follow</button>` : ""}
              ${p.location ? `<div class="loc">${esc(p.location)}</div>` : ""}</div>
            <button data-action="post-menu" data-id="${p.id}" aria-label="More options">${icon("more")}</button>
          </div>
          <div class="comments">
            ${p.caption ? `<div class="comment">${avatarLink(p.user, "sm")}<div class="body"><a class="user bold" href="#/profile/${esc(p.user)}">${esc(p.user)}</a> ${richText(p.caption)}<div class="meta"><span>${ago(p.time)}</span></div></div></div>` : ""}
            ${p.comments.map((c) => `
              <div class="comment">
                ${avatarLink(c.user, "sm")}
                <div class="body">
                  <a class="user bold" href="#/profile/${esc(c.user)}">${esc(c.user)}</a> ${richText(c.text)}
                  <div class="meta"><span>${ago(c.time)}</span>${c.likes ? `<span>${c.likes} like${c.likes > 1 ? "s" : ""}</span>` : ""}
                    <button data-action="reply" data-user="${esc(c.user)}">Reply</button>
                    ${c.user === "me" || p.user === "me" ? `<button data-action="del-comment" data-id="${p.id}" data-cid="${c.id}">Delete</button>` : ""}
                  </div>
                </div>
                <button class="c-like ${c.liked ? "liked" : ""}" data-action="like-comment" data-id="${p.id}" data-cid="${c.id}" aria-label="Like comment">${icon("heart")}</button>
              </div>`).join("") || (p.caption ? "" : `<div class="empty"><h2 style="font-size:22px">No comments yet.</h2><p>Start the conversation.</p></div>`)}
          </div>
          <div class="foot">
            ${actionsBar(p)}
            <button class="likes" data-action="likes-list" data-id="${p.id}">${fmtNum(p.likes)} likes</button>
            <div class="time">${ago(p.time, true)}</div>
            <form class="add-comment" data-action="comment" data-id="${p.id}">
              <input name="text" placeholder="Add a comment…" autocomplete="off" aria-label="Add a comment" />
              <button type="submit" disabled>Post</button>
            </form>
          </div>
        </div>
      </div>`;
    if (m.hidden || m.dataset.post !== id) openModal(html, { kind: "post" });
    else {
      const scroller = m.querySelector(".comments");
      const st = scroller ? scroller.scrollTop : 0;
      m.innerHTML = `<button class="modal-close" data-action="close-modal" aria-label="Close">${icon("close")}</button>${html}`;
      const s2 = m.querySelector(".comments"); if (s2) s2.scrollTop = st;
    }
    m.dataset.post = id;
  }
  function openPost(id) {
    if (!postBy(id)) { toast("Post not found"); return; }
    renderPostModal(id);
  }

  function listDialog(title, usernames) {
    openModal(`
      <div class="dialog listdlg" role="dialog" aria-label="${esc(title)}">
        <div class="create-head"><span></span>${esc(title)}<button data-action="close-modal" aria-label="Close" style="color:var(--text)">${icon("close")}</button></div>
        <div class="list">
          ${usernames.length ? usernames.map((n) => {
            const u = userBy(n);
            return `<div class="sugg">${avatarLink(n, "md")}<div class="who"><a href="#/profile/${esc(n)}" data-action="close-modal-link">${esc(n)}</a>${verified(u)}<small>${esc(u?.name)}</small></div>${followBtn(n)}</div>`;
          }).join("") : `<p class="muted" style="text-align:center;padding:20px">Nobody here yet.</p>`}
        </div>
      </div>`);
  }

  /* ================= stories ================= */
  let storyState = null;
  const STORY_MS = 5000;
  function openStory(username) {
    const order = [...state.stories].sort((a, b) => a.seen - b.seen);
    const idx = order.findIndex((s) => s.user === username);
    if (idx < 0) return;
    storyState = { order: order.map((s) => s.user), ui: idx, si: 0, start: 0, elapsed: 0, raf: 0, paused: false };
    openModal(`<div class="story-viewer" id="sv" role="dialog" aria-label="Story"></div>`, { kind: "story" });
    showSlide();
  }
  function showSlide() {
    const s = state.stories.find((x) => x.user === storyState.order[storyState.ui]);
    const u = userBy(s.user);
    const sv = $("#sv");
    if (!sv) return;
    sv.innerHTML = `
      <div class="story-bars">${s.slides.map((_, i) => `<div><i style="width:${i < storyState.si ? 100 : 0}%"></i></div>`).join("")}</div>
      <div class="story-top">
        <img class="avatar sm" src="${esc(u.avatar)}" alt="" />
        <a class="bold" href="#/profile/${esc(u.username)}" data-action="close-modal-link">${esc(u.username)}</a>
        <span style="opacity:.8">${(storyState.ui * 3 + storyState.si + 1) % 23 + 1}h</span>
      </div>
      <img src="${esc(s.slides[storyState.si])}" alt="Story by ${esc(u.username)}" />
      <div class="story-nav"><button data-action="story-prev" aria-label="Previous"></button><button data-action="story-next" aria-label="Next"></button></div>
      ${s.user !== "me" ? `<form class="story-reply" data-action="story-reply"><input placeholder="Reply to ${esc(u.username)}…" aria-label="Reply" /></form>` : ""}`;
    s.seen = true;
    save();
    storyState.elapsed = 0;
    storyState.start = performance.now();
    cancelAnimationFrame(storyState.raf);
    tick();
  }
  function tick() {
    if (!storyState) return;
    const bar = document.querySelectorAll("#sv .story-bars i")[storyState.si];
    const now = performance.now();
    if (!storyState.paused) {
      storyState.elapsed += now - storyState.start;
    }
    storyState.start = now;
    if (bar) bar.style.width = Math.min(100, (storyState.elapsed / STORY_MS) * 100) + "%";
    if (storyState.elapsed >= STORY_MS) return storyStep(1);
    storyState.raf = requestAnimationFrame(tick);
  }
  function storyStep(dir) {
    const s = state.stories.find((x) => x.user === storyState.order[storyState.ui]);
    storyState.si += dir;
    if (storyState.si >= s.slides.length) { storyState.ui++; storyState.si = 0; }
    else if (storyState.si < 0) {
      storyState.ui--;
      if (storyState.ui < 0) { storyState.ui = 0; storyState.si = 0; }
      else storyState.si = 0;
    }
    if (storyState.ui >= storyState.order.length) { closeModal(); refresh(); return; }
    showSlide();
  }
  function stopStory() {
    if (storyState) { cancelAnimationFrame(storyState.raf); storyState = null; }
  }

  /* ================= create post ================= */
  const FILTERS = [["Normal", ""], ["Clarendon", "contrast(1.2) saturate(1.35)"], ["Juno", "sepia(.25) saturate(1.6) hue-rotate(-10deg)"], ["Moon", "grayscale(1) contrast(1.1) brightness(1.1)"], ["Lark", "brightness(1.1) saturate(.85) contrast(.95)"], ["Reyes", "sepia(.22) brightness(1.1) contrast(.85) saturate(.75)"]];
  let draft = null;
  function openCreate() {
    draft = { image: null, filter: "" };
    openModal(`
      <div class="dialog create" role="dialog" aria-label="Create new post">
        <div class="create-head"><span style="width:40px"></span>Create new post<button id="share-btn" data-action="publish" disabled>Share</button></div>
        <div class="create-body" id="create-body">
          <label class="drop" id="drop">
            ${icon("gallery")}
            <p>Drag photos here</p>
            <span class="btn primary">Select from computer</span>
            <input type="file" accept="image/*" id="file-input" hidden />
            <span class="muted" style="font-size:12px">…or <button type="button" class="link-btn" data-action="random-photo">use a random photo</button></span>
          </label>
        </div>
      </div>`);
    const drop = $("#drop");
    ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("drag"); }));
    drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) readImage(f); });
    $("#file-input").addEventListener("change", (e) => { const f = e.target.files[0]; if (f) readImage(f); });
  }
  function readImage(file) {
    if (!file.type.startsWith("image/")) return toast("Please choose an image file.");
    const reader = new FileReader();
    reader.onload = () => {
      // Downscale to keep localStorage happy
      const img = new Image();
      img.onload = () => {
        const max = 1080, scale = Math.min(1, max / Math.max(img.width, img.height));
        const c = document.createElement("canvas");
        c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        setDraftImage(c.toDataURL("image/jpeg", 0.82));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  }
  function setDraftImage(src) {
    draft.image = src;
    $("#create-body").innerHTML = `
      <div class="create-preview"><img id="preview" src="${esc(src)}" alt="Preview" /></div>
      <div class="create-form">
        <div class="me-row" style="padding:0">${avatarLink("me", "sm")}<div class="who bold">${esc(me().username)}</div></div>
        <textarea id="cap" rows="6" maxlength="2200" placeholder="Write a caption… Use #tags and @mentions" autofocus></textarea>
        <input id="loc" placeholder="Add location" maxlength="60" />
        <div><div class="bold" style="margin-bottom:8px">Filter</div>
          <div class="filters">${FILTERS.map(([n, f], i) => `<button type="button" class="${i === 0 ? "active" : ""}" data-action="filter" data-filter="${esc(f)}">${n}</button>`).join("")}</div>
        </div>
      </div>`;
    $("#share-btn").disabled = false;
    $("#cap").focus();
  }
  function publish() {
    if (!draft?.image) return;
    const post = {
      id: "p" + uid(), user: "me", image: draft.image, filter: draft.filter,
      caption: $("#cap").value.trim(), location: $("#loc").value.trim(),
      likes: 0, liked: false, saved: false, time: Date.now(), comments: [],
    };
    state.posts.unshift(post);
    save();
    closeModal();
    toast("Your post has been shared.");
    if (location.hash === "#/profile/me") refresh(); else location.hash = "#/profile/me";
  }

  /* ================= edit profile ================= */
  function openEditProfile() {
    const m = me();
    openModal(`
      <div class="dialog edit" role="dialog" aria-label="Edit profile">
        <div class="create-head"><span style="width:40px"></span>Edit profile<button data-action="close-modal" style="color:var(--text)" aria-label="Close">${icon("close")}</button></div>
        <form id="edit-form">
          <div class="avatar-pick">
            <img class="avatar lg" id="ep-avatar" src="${esc(m.avatar)}" alt="" />
            <div class="who"><div class="bold">${esc(m.username)}</div><small>${esc(m.name)}</small></div>
            <label class="btn primary">Change photo<input type="file" accept="image/*" id="ep-file" hidden /></label>
          </div>
          <div class="field"><label for="ep-name">Name</label><input id="ep-name" maxlength="40" value="${esc(m.name)}" /></div>
          <div class="field"><label for="ep-bio">Bio</label><textarea id="ep-bio" rows="4" maxlength="150">${esc(m.bio)}</textarea></div>
          <button class="btn primary" type="submit">Submit</button>
        </form>
      </div>`);
    let avatar = m.avatar;
    $("#ep-file").addEventListener("change", (e) => {
      const f = e.target.files[0]; if (!f) return;
      const r = new FileReader();
      r.onload = () => {
        const img = new Image();
        img.onload = () => {
          const c = document.createElement("canvas"), s = Math.min(img.width, img.height);
          c.width = c.height = 300;
          c.getContext("2d").drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 300, 300);
          avatar = c.toDataURL("image/jpeg", 0.85);
          $("#ep-avatar").src = avatar;
        };
        img.src = r.result;
      };
      r.readAsDataURL(f);
    });
    $("#edit-form").addEventListener("submit", (e) => {
      e.preventDefault();
      m.name = $("#ep-name").value.trim() || m.name;
      m.bio = $("#ep-bio").value;
      m.avatar = avatar;
      save(); closeModal(); refresh(); toast("Profile saved.");
    });
  }

  /* ================= panels ================= */
  let panelKind = null;
  function openPanel(kind) {
    const panel = $("#panel");
    if (panelKind === kind) return closePanel();
    panelKind = kind;
    if (kind === "search") {
      panel.innerHTML = `<h2>Search</h2><div class="search-box"><input id="q" placeholder="Search users or #tags" autocomplete="off" aria-label="Search" /></div><div class="results" id="results"></div>`;
      const q = $("#q");
      const run = () => {
        const v = q.value.trim().toLowerCase();
        const res = $("#results");
        if (!v) {
          res.innerHTML = `<div class="section">Popular accounts</div>` + state.users.filter((u) => u.username !== "me").sort((a, b) => b.followers - a.followers).slice(0, 6).map(userRow).join("");
          return;
        }
        if (v.startsWith("#")) {
          const tag = v.slice(1);
          const tags = {};
          state.posts.forEach((p) => (p.caption.match(/#\w+/g) || []).forEach((t) => {
            t = t.slice(1).toLowerCase(); if (t.includes(tag)) tags[t] = (tags[t] || 0) + 1;
          }));
          const keys = Object.keys(tags);
          res.innerHTML = keys.length ? keys.map((t) => `<a class="row" href="#/explore?tag=${esc(t)}"><span class="avatar md" style="display:flex;align-items:center;justify-content:center;border:1px solid var(--border);font-size:20px">#</span><div class="who"><div class="bold">#${esc(t)}</div><small class="muted">${tags[t]} post${tags[t] > 1 ? "s" : ""}</small></div></a>`).join("") : `<p class="muted" style="padding:24px">No results found.</p>`;
          return;
        }
        const users = state.users.filter((u) => u.username.toLowerCase().includes(v) || u.name.toLowerCase().includes(v));
        res.innerHTML = users.length ? users.map(userRow).join("") : `<p class="muted" style="padding:24px">No results found.</p>`;
      };
      q.addEventListener("input", run);
      run();
      setTimeout(() => q.focus(), 50);
    } else {
      const groups = { Today: [], "This week": [], Earlier: [] };
      state.notifications.forEach((n) => {
        const h = (Date.now() - n.time) / 3600000;
        groups[h < 24 ? "Today" : h < 168 ? "This week" : "Earlier"].push(n);
      });
      panel.innerHTML = `<h2>Notifications</h2><div class="results">${Object.entries(groups).filter(([, v]) => v.length).map(([k, v]) => `
        <div class="section">${k}</div>
        ${v.map((n) => {
          const p = n.post && postBy(n.post);
          return `<div class="row">${avatarLink(n.user, "md")}<div class="who"><a class="bold" href="#/profile/${esc(n.user)}">${esc(n.user)}</a> ${esc(n.text)} <span class="muted">${ago(n.time)}</span></div>
            ${p ? `<button data-action="open-post" data-id="${p.id}"><img class="thumb" src="${esc(p.image)}" alt="" /></button>` : n.type === "follow" ? followBtn(n.user) : ""}</div>`;
        }).join("")}`).join("")}</div>`;
    }
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
  }
  function userRow(u) {
    return `<a class="row" href="#/profile/${esc(u.username)}"><img class="avatar md" src="${esc(u.avatar)}" alt="" /><div class="who"><div class="bold">${esc(u.username)}${verified(u)}</div><small class="muted">${esc(u.name)} • ${fmtNum(u.followers)} followers</small></div></a>`;
  }
  function closePanel() {
    panelKind = null;
    const panel = $("#panel");
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
  }

  /* ================= actions ================= */
  function toggleLike(id, forceOn = false) {
    const p = postBy(id);
    if (forceOn && p.liked) return;
    p.liked = !p.liked;
    p.likes += p.liked ? 1 : -1;
    save();
    // Update all like buttons for this post in place (feed + modal)
    document.querySelectorAll(`[data-action="like"][data-id="${id}"]`).forEach((b) => {
      b.classList.toggle("liked", p.liked);
      b.setAttribute("aria-pressed", p.liked);
      b.setAttribute("aria-label", p.liked ? "Unlike" : "Like");
      if (p.liked) { b.classList.remove("like-anim"); void b.offsetWidth; b.classList.add("like-anim"); }
    });
    document.querySelectorAll(`[data-action="likes-list"][data-id="${id}"]`).forEach((b) => (b.textContent = `${fmtNum(p.likes)} likes`));
  }
  function toggleSave(id) {
    const p = postBy(id);
    p.saved = !p.saved;
    save();
    document.querySelectorAll(`[data-action="save"][data-id="${id}"]`).forEach((b) => {
      b.classList.toggle("saved", p.saved);
      b.setAttribute("aria-pressed", p.saved);
    });
    toast(p.saved ? "Saved to your collection." : "Removed from saved.");
  }
  function toggleFollow(username) {
    const i = state.following.indexOf(username);
    if (i >= 0) state.following.splice(i, 1); else state.following.push(username);
    save();
    toast(i >= 0 ? `Unfollowed ${username}` : `Following ${username}`);
    refresh();
    if (!$("#modal").hidden && $("#modal").dataset.kind !== "post") {
      document.querySelectorAll(`#modal [data-action="follow"][data-user="${CSS.escape(username)}"]`).forEach((b) => {
        const f = isFollowing(username);
        b.textContent = f ? "Following" : "Follow";
        b.className = f ? "btn" : "btn primary";
      });
    }
    if (panelKind === "notifications") { panelKind = null; openPanel("notifications"); }
  }
  let lastTap = 0;
  function doubleTapLike(el, id) {
    toggleLike(id, true);
    const h = el.querySelector(".big-heart");
    if (h) { h.classList.remove("pop"); void h.offsetWidth; h.classList.add("pop"); }
  }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-action]");
    if (!t) {
      if (panelKind && !e.target.closest("#panel")) closePanel();
      return;
    }
    const a = t.dataset.action, id = t.dataset.id, user = t.dataset.user;
    if (panelKind && !t.closest("#panel") && a !== "search" && a !== "notifications") closePanel();

    switch (a) {
      case "like": toggleLike(id); break;
      case "save": toggleSave(id); break;
      case "dbl-like": {
        const now = Date.now();
        if (now - lastTap < 320) { doubleTapLike(t, id); lastTap = 0; } else lastTap = now;
        break;
      }
      case "open-post": closePanel(); openPost(id); break;
      case "share": {
        const url = `${location.origin}${location.pathname}#/p/${id}`;
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(() => toast("Link copied to clipboard."), () => toast(url));
        else toast(url);
        break;
      }
      case "follow": toggleFollow(user); break;
      case "story": openStory(user); break;
      case "story-next": storyStep(1); break;
      case "story-prev": storyStep(-1); break;
      case "close-modal": closeModal(); break;
      case "close-modal-link": closeModal(); break;
      case "create": closePanel(); openCreate(); break;
      case "random-photo": e.preventDefault(); setDraftImage(`https://picsum.photos/seed/${uid()}/900/900`); break;
      case "filter":
        draft.filter = t.dataset.filter;
        $("#preview").style.filter = draft.filter;
        t.parentElement.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === t));
        break;
      case "publish": publish(); break;
      case "edit-profile": openEditProfile(); break;
      case "theme": state.theme = state.theme === "dark" ? "light" : "dark"; save(); applyTheme(); break;
      case "search": openPanel("search"); break;
      case "notifications": openPanel("notifications"); break;
      case "tab": profileTab = t.dataset.tab; refresh(); break;
      case "likes-list": {
        const p = postBy(id);
        const names = state.users.filter((u) => u.username !== p.user).map((u) => u.username).filter((n) => n !== "me" || p.liked);
        listDialog("Likes", names);
        break;
      }
      case "followers": {
        const names = user === "me" ? state.users.filter((u) => u.username !== "me").slice(0, 6).map((u) => u.username)
          : [...(isFollowing(user) ? ["me"] : []), ...state.users.filter((u) => u.username !== user && u.username !== "me").slice(0, 5).map((u) => u.username)];
        listDialog("Followers", names);
        break;
      }
      case "following": {
        const names = user === "me" ? [...state.following] : state.users.filter((u) => u.username !== user && u.username !== "me").slice(2, 7).map((u) => u.username);
        listDialog("Following", names);
        break;
      }
      case "message": toast(`Messaging isn't available in this demo.`); break;
      case "reply": {
        const input = t.closest(".side")?.querySelector('.add-comment input');
        if (input) { input.value = `@${user} `; input.focus(); input.dispatchEvent(new Event("input", { bubbles: true })); }
        break;
      }
      case "like-comment": {
        const c = postBy(id).comments.find((x) => x.id === t.dataset.cid);
        c.liked = !c.liked; c.likes = (c.likes || 0) + (c.liked ? 1 : -1);
        save(); renderPostModal(id);
        break;
      }
      case "del-comment": {
        const p = postBy(id);
        p.comments = p.comments.filter((x) => x.id !== t.dataset.cid);
        save(); refresh();
        break;
      }
      case "post-menu": {
        const p = postBy(id);
        const fromModal = $("#modal").dataset.kind === "post" ? id : "";
        openModal(`
          <div class="dialog menu" role="dialog" aria-label="Post options">
            ${p.user === "me" ? `<button class="danger" data-action="delete-post" data-id="${id}">Delete</button>`
              : isFollowing(p.user) ? `<button class="danger" data-action="menu-unfollow" data-user="${esc(p.user)}">Unfollow</button>` : ""}
            <button data-action="menu-open" data-id="${id}">Go to post</button>
            <button data-action="share" data-id="${id}">Copy link</button>
            <a href="#/profile/${esc(p.user)}" data-action="close-modal-link" style="display:block;padding:14px;border-top:1px solid var(--border);text-align:center">About this account</a>
            <button data-action="${fromModal ? "menu-open" : "close-modal"}" data-id="${fromModal}">Cancel</button>
          </div>`);
        break;
      }
      case "menu-open": closeModal(); if (id) openPost(id); break;
      case "menu-unfollow": closeModal(); toggleFollow(user); break;
      case "delete-post":
        if (confirm("Delete this post? This can't be undone.")) {
          state.posts = state.posts.filter((p) => p.id !== id);
          save(); closeModal(); refresh(); toast("Post deleted.");
        }
        break;
      case "reset":
        if (confirm("Reset all demo data? Your posts and edits will be lost.")) {
          localStorage.removeItem(KEY); load(); applyTheme(); route(); toast("Demo data reset.");
        }
        break;
    }
  });

  // Close modal when clicking the backdrop itself
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

  // Enable "Post" button only when there's text
  document.addEventListener("input", (e) => {
    const form = e.target.closest('form[data-action="comment"]');
    if (form) form.querySelector("button").disabled = !e.target.value.trim();
  });

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (form.dataset.action === "comment") {
      e.preventDefault();
      const input = form.querySelector("input");
      const text = input.value.trim();
      if (!text) return;
      const p = postBy(form.dataset.id);
      p.comments.push({ id: "c" + uid(), user: "me", text, time: Date.now(), likes: 0 });
      save();
      input.value = "";
      refresh();
      if ($("#modal").dataset.post === p.id) {
        const sc = $("#modal .comments"); if (sc) sc.scrollTop = sc.scrollHeight;
      }
    } else if (form.dataset.action === "story-reply") {
      e.preventDefault();
      const input = form.querySelector("input");
      if (input.value.trim()) { toast("Reply sent."); input.value = ""; input.blur(); }
    }
  });

  // Pause story while typing a reply or holding down
  document.addEventListener("focusin", (e) => { if (storyState && e.target.closest(".story-reply")) storyState.paused = true; });
  document.addEventListener("focusout", (e) => { if (storyState && e.target.closest(".story-reply")) storyState.paused = false; });
  document.addEventListener("pointerdown", (e) => { if (storyState && e.target.closest(".story-nav")) storyState.paused = true; });
  document.addEventListener("pointerup", () => { if (storyState && !document.activeElement?.closest(".story-reply")) storyState.paused = false; });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (!$("#modal").hidden) closeModal(); else closePanel();
    }
    if (storyState && !e.target.closest("input")) {
      if (e.key === "ArrowRight") storyStep(1);
      if (e.key === "ArrowLeft") storyStep(-1);
    }
  });

  window.addEventListener("hashchange", () => {
    if (!$("#modal").hidden && !location.hash.startsWith("#/p/")) closeModal();
    route();
    if (!location.hash.startsWith("#/p/")) scrollTo(0, 0);
  });

  /* ================= boot ================= */
  load();
  hydrateIcons();
  applyTheme();
  route();
})();
