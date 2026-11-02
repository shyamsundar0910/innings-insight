(() => {
  const target = document.getElementById('substack-articles');
  if (!target) return;
  const add = (el, tag, text, cls) => {
    const child = document.createElement(tag);
    if (cls) child.className = cls;
    child.textContent = text || '';
    el.appendChild(child);
    return child;
  };
  fetch('articles.json', { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw new Error('Article feed unavailable');
      return response.json();
    })
    .then(data => {
      const posts = Array.isArray(data.posts) ? data.posts.slice(0, 6) : [];
      if (!posts.length) return;
      const cards = [];
      for (const post of posts) {
        if (!post || typeof post.url !== 'string' || !post.url.startsWith('https://inningsinsiders.substack.com/')) continue;
        const a = document.createElement('a');
        a.className = 'article-preview';
        a.href = post.url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        if (typeof post.image === 'string' && /^https:\/\//.test(post.image)) {
          const img = document.createElement('img');
          img.className = 'article-preview-cover';
          img.src = post.image;
          img.alt = '';
          img.loading = 'lazy';
          img.referrerPolicy = 'no-referrer';
          a.appendChild(img);
        }
        const body = add(a, 'div', '', 'article-preview-body');
        const date = post.date && /^\d{4}-\d{2}-\d{2}$/.test(post.date)
          ? new Date(post.date + 'T12:00:00Z').toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'})
          : 'Innings Insiders';
        add(body, 'span', date, 'smallcaps');
        add(body, 'h3', post.title);
        add(body, 'p', post.description || 'Read the full analysis on Innings Insiders.');
        add(body, 'span', 'Read on Substack →', 'card-link');
        cards.push(a);
      }
      if (cards.length) target.replaceChildren(...cards);
    })
    .catch(error => console.warn('Substack articles unavailable:', error));
})();
