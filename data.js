/* Seed data for Lolgram. Everything is fictional. */
(function () {
  const img = (seed, w = 640, h = 640) => `https://picsum.photos/seed/${seed}/${w}/${h}`;
  const now = Date.now();
  const H = 3600 * 1000;

  const users = [
    { username: "me", name: "You", bio: "Just joined Lolgram ✨\nEdit me from the profile page.", avatar: img("me-avatar", 150, 150), followers: 128, following: 180, verified: false },
    { username: "wanderlust.maya", name: "Maya Torres", bio: "Chasing sunsets 🌅 | 34 countries\nTravel tips below ⬇️", avatar: img("maya", 150, 150), followers: 48200, following: 512, verified: true },
    { username: "chef_arjun", name: "Arjun Mehta", bio: "Home cook. Spice enthusiast. 🌶️\nRecipes every Sunday.", avatar: img("arjun", 150, 150), followers: 12890, following: 301, verified: false },
    { username: "pixel.paws", name: "Pixel & Paws", bio: "Two cats, one camera 🐾", avatar: img("paws", 150, 150), followers: 97100, following: 88, verified: true },
    { username: "urban.lens", name: "Leo Kim", bio: "Street photography · Seoul → Berlin", avatar: img("leo", 150, 150), followers: 23400, following: 640, verified: false },
    { username: "green.thumb", name: "Priya Nair", bio: "Plant mom of 74 🌿", avatar: img("priya", 150, 150), followers: 5600, following: 420, verified: false },
    { username: "trail.runner", name: "Sam Okafor", bio: "Ultra runner. Mountains > everything.", avatar: img("sam", 150, 150), followers: 8800, following: 230, verified: false },
    { username: "studio.noor", name: "Noor Haddad", bio: "Ceramics & slow living ☕", avatar: img("noor", 150, 150), followers: 31200, following: 199, verified: true },
    { username: "bytes.and.beats", name: "Dev Patel", bio: "Code by day, synths by night 🎹", avatar: img("dev", 150, 150), followers: 4100, following: 377, verified: false },
  ];

  const captions = [
    ["wanderlust.maya", "Golden hour hits different up here 🏔️ #travel #mountains", "mountain1"],
    ["chef_arjun", "Sunday biryani is ready. Recipe in comments? 🍛", "food1"],
    ["pixel.paws", "Caught mid-zoomies. No regrets. 🐈", "cat1"],
    ["urban.lens", "Rain, neon, and a stranger with an umbrella. #streetphotography", "city1"],
    ["green.thumb", "New leaf unlocked 🌱 Monstera update!", "plant1"],
    ["trail.runner", "42km of pure mud. Loved every second.", "trail1"],
    ["studio.noor", "Fresh out of the kiln. Which glaze is your favourite?", "ceramic1"],
    ["bytes.and.beats", "Late night jam session setup 🎛️", "synth1"],
    ["wanderlust.maya", "Found the quietest beach in the world 🌊", "beach1"],
    ["pixel.paws", "Professional box inspector at work.", "cat2"],
    ["urban.lens", "Morning commute, frozen in time.", "city2"],
    ["chef_arjun", "Homemade pasta night 🍝 Flour everywhere.", "pasta1"],
  ];

  const commentPool = [
    "This is stunning 😍", "Wow!! 🔥🔥", "Need this in my life", "Where is this?",
    "Absolutely love it", "Goals 🙌", "Saving this!", "Incredible shot", "So good 👏", "Teach me your ways",
  ];

  const posts = captions.map(([user, caption, seed], i) => {
    const commenters = users.filter((u) => u.username !== user && u.username !== "me");
    const comments = Array.from({ length: (i % 3) + 1 }, (_, j) => ({
      id: `c${i}-${j}`,
      user: commenters[(i + j * 3) % commenters.length].username,
      text: commentPool[(i * 3 + j) % commentPool.length],
      time: now - (i + 1) * H + j * 600000,
      likes: (i * 7 + j * 3) % 20,
    }));
    return {
      id: `p${i + 1}`,
      user,
      image: img(seed, 900, 900),
      caption,
      likes: 120 + ((i * 7919) % 9000),
      liked: false,
      saved: false,
      time: now - (i * 5 + 1) * H,
      location: i % 3 === 0 ? ["Swiss Alps", "Lisbon, Portugal", "Kyoto, Japan", "Cape Town"][i % 4] : "",
      comments,
    };
  });

  // A few posts for "me" so the profile isn't empty
  ["myfirst", "mysecond", "mythird"].forEach((seed, i) => {
    posts.push({
      id: `pm${i + 1}`, user: "me", image: img(seed, 900, 900),
      caption: ["Hello Lolgram 👋", "Weekend vibes", "Coffee first ☕"][i],
      likes: 20 + i * 11, liked: false, saved: false,
      time: now - (i + 2) * 24 * H, location: "", comments: [],
    });
  });

  const stories = users.slice(1).map((u, i) => ({
    user: u.username,
    seen: false,
    slides: Array.from({ length: (i % 3) + 1 }, (_, j) => img(`story-${u.username}-${j}`, 540, 960)),
  }));

  const notifications = [
    { user: "wanderlust.maya", type: "like", text: "liked your photo.", time: now - 0.3 * H, post: "pm1" },
    { user: "pixel.paws", type: "follow", text: "started following you.", time: now - 2 * H },
    { user: "chef_arjun", type: "comment", text: "commented: Looks great! 🙌", time: now - 5 * H, post: "pm2" },
    { user: "studio.noor", type: "like", text: "liked your photo.", time: now - 26 * H, post: "pm3" },
    { user: "trail.runner", type: "follow", text: "started following you.", time: now - 50 * H },
  ];

  window.SEED = { users, posts, stories, notifications, following: ["wanderlust.maya", "chef_arjun", "pixel.paws", "urban.lens"] };
})();
