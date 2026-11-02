const test = require('node:test');
const assert = require('node:assert/strict');
const {LINK, extractAcceptance} = require('../.github/scripts/acceptance.cjs');

const issue = body => ({user: {login: 'owner'}, labels: [{name: 'agent:approved'}], body});

test('extracts the owner acceptance block', () => {
  assert.equal(extractAcceptance(issue('Text\n```js acceptance\nassert(1);\n```\n'), 'owner'), 'assert(1);\n');
});

test('refuses missing, unapproved or non-owner acceptance', () => {
  assert.throws(() => extractAcceptance(issue('no block'), 'owner'), /no js acceptance/);
  assert.throws(() => extractAcceptance({...issue('```js acceptance\nx\n```'), user: {login: 'bot'}}, 'owner'), /owner-authored/);
  assert.throws(() => extractAcceptance({...issue('```js acceptance\nx\n```'), labels: []}, 'owner'), /not approved/);
});

test('finds the closing issue reference', () => {
  assert.equal(LINK.exec('Implements it.\n\nCloses #6')[1], '6');
  assert.equal(LINK.exec('see #6'), null);
});
