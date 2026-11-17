// Driver portraits: free-licensed Wikimedia Commons photos listed in drivers/credits.json
// (made by scripts/fetch_driver_photos.py). Kept out of the main bundle so its text ids stay stable.
const ko = document.documentElement.lang === 'ko';

const style = document.createElement('style');
style.textContent = `
.tpd__drv.has-face{grid-template-columns:auto auto 1fr;grid-template-areas:"face first nat""face last last"}
.tpd__face{grid-area:face;align-self:center;width:clamp(52px,4vw + 30px,76px);aspect-ratio:1;margin-right:6px;border-radius:50%;object-fit:cover;object-position:50% 22%;background:var(--tp-faint)}`;
document.head.append(style);

fetch('./drivers/credits.json').then(r => r.json()).then(data => {
  const addFaces = () => {
    for (const li of document.querySelectorAll('.tpd__drv:not([data-face])')) {
      li.dataset.face = '';
      const name = `${li.querySelector('.tpd__first').textContent} ${li.querySelector('.tpd__last').textContent}`.trim();
      const d = data[name];
      if (!d) continue;
      const img = Object.assign(document.createElement('img'), {
        className: 'tpd__face', src: d.src, alt: name, loading: 'lazy', decoding: 'async',
        title: `${ko ? '사진' : 'Photo'}: ${d.author}, ${d.license}`,
      });
      li.classList.add('has-face');
      li.prepend(img);
    }
  };
  addFaces();
  // team pages are rendered on navigation, so watch for new driver lists
  new MutationObserver(addFaces).observe(document.body, { childList: true, subtree: true });

  // credits in the footer, same format as the car photo credits; built with textContent (API text is untrusted)
  const list = document.querySelector('[data-face-credits]');
  if (!list) return;
  const names = Object.keys(data).sort();
  document.querySelector('[data-face-count]').textContent = names.length;
  for (const name of names) {
    const d = data[name], li = document.createElement('li'), b = document.createElement('span'), a = document.createElement('a');
    b.textContent = name;
    Object.assign(a, { href: d.page, rel: 'noopener', textContent: d.license });
    li.append(b, ` ${d.author}, `, a);
    list.append(li);
  }
}).catch(() => {}); // portraits are decoration: the page works without them
