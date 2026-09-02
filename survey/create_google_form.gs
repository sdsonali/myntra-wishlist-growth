/**
 * Myntra wishlist — primary research form (dormant / unsold items).
 *
 * Segment: monthly+ fashion shoppers who still have wishlist items they have
 * not purchased. Part 3 of the brief is about what is stopping conversion,
 * so the interview item must be sitting on the wishlist — not one they already bought.
 *
 * The "purchased a wishlisted item in the last 30 days" question is diagnostic
 * only. Both Yes and No continue. Do not use it as a gate.
 *
 * HOW TO UPDATE THE LIVE FORM (same URL as the deck):
 * 1. https://script.google.com → New project (or the script already bound to the form)
 * 2. Paste this file → Save
 * 3. Run rebuildExistingDormantForm — this wipes questions on
 *    form ID 1pAxwhdTkoDF-I8U6HfzbnQ91UW9nkpmxIaEo9-qTEvQ and rebuilds them.
 *    Old responses stay in the linked Sheet but will not match the new columns.
 * 4. Approve FormApp permissions if asked → Logs should print the same live URL.
 *
 * HOW TO CREATE A BRAND-NEW FORM INSTEAD:
 * Run createDormantWishlistInterviewForm (new URL — then update the deck).
 *
 * Do NOT import responses/Wishlist shopping decisions.csv — those rows are a
 * synthetic converter pilot tied to the MVP catalog, not this screener.
 */

var LIVE_FORM_ID = '1pAxwhdTkoDF-I8U6HfzbnQ91UW9nkpmxIaEo9-qTEvQ';

function createDormantWishlistInterviewForm() {
  var form = FormApp.create('Myntra wishlist — items you saved but have not bought');
  buildDormantInterviewForm_(form);
  Logger.log('Live form: ' + form.getPublishedUrl());
  Logger.log('Edit form: ' + form.getEditUrl());
}

/**
 * Rebuilds the existing published form in place so the viewform / edit URLs
 * in the deck do not change.
 */
function rebuildExistingDormantForm() {
  var form = FormApp.openById(LIVE_FORM_ID);
  clearFormItems_(form);
  form.setTitle('Myntra wishlist — items you saved but have not bought');
  form.setConfirmationMessage(
    'Thanks. If you ticked the follow-up chat, we may email you for a 15–20 min call.'
  );
  buildDormantInterviewForm_(form);
  Logger.log('Rebuilt form ' + LIVE_FORM_ID);
  Logger.log('Live form: ' + form.getPublishedUrl());
  Logger.log('Edit form: ' + form.getEditUrl());
}

/**
 * Page-branching choices cannot be deleted until go-to-page is cleared.
 * "Invalid data updating form" is what Google throws if you skip that.
 */
function clearFormItems_(form) {
  var items = form.getItems();
  var i;
  var item;
  var type;
  var choices;
  var values;
  var j;

  for (i = 0; i < items.length; i++) {
    item = items[i];
    type = item.getType();
    if (type === FormApp.ItemType.PAGE_BREAK) {
      try {
        item.asPageBreakItem().setGoToPage(FormApp.PageNavigationType.CONTINUE);
      } catch (e1) {}
    }
    if (type === FormApp.ItemType.MULTIPLE_CHOICE) {
      choices = item.asMultipleChoiceItem().getChoices();
      values = [];
      for (j = 0; j < choices.length; j++) {
        values.push(choices[j].getValue());
      }
      if (values.length) {
        item.asMultipleChoiceItem().setChoiceValues(values);
      }
    }
  }

  items = form.getItems();
  for (i = items.length - 1; i >= 0; i--) {
    try {
      form.deleteItem(items[i]);
    } catch (e2) {}
  }

  items = form.getItems();
  for (i = items.length - 1; i >= 0; i--) {
    form.deleteItem(i);
  }
}

/** @deprecated Use createDormantWishlistInterviewForm */
function createMvpWishlistInterviewForm() {
  createDormantWishlistInterviewForm();
}

function buildDormantInterviewForm_(form) {
  form.setProgressBar(true);
  form.setShowLinkToRespondAgain(false);
  form.setAllowResponseEdits(false);
  form.setDescription(
    'Takes about 6–8 minutes. We are studying why fashion items sit on a wishlist ' +
      'without being purchased.\n\n' +
    'There is no sales pitch. Please answer about ONE specific item that is still ' +
      'on your wishlist (Myntra or similar) and that you have not bought. Use that ' +
      'same item for every question.\n\n' +
    'If you have several sitting there, pick the one you were most likely to buy.'
  );

  // --- Page 1: frequency ---
  var qFreq = form.addMultipleChoiceItem()
    .setTitle('How often do you shop for fashion/clothing online on apps like Myntra?')
    .setRequired(true);

  var sUnsold = form.addPageBreakItem()
    .setTitle('Items still on your wishlist')
    .setHelpText(
      'We need people who still have at least one saved item they have not purchased.'
    );

  var qUnsold = form.addMultipleChoiceItem()
    .setTitle(
      'Do you currently have at least one fashion item on a wishlist that you have ' +
      'not purchased?'
    )
    .setRequired(true);

  var sExit = form.addPageBreakItem()
    .setTitle('Thanks for your time')
    .setHelpText(
      'This interview is for shoppers who still have unsold wishlist items. ' +
      'You are not in that segment right now.'
    );
  sExit.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  // --- About you (captures the segment; does not exit) ---
  var sAbout = form.addPageBreakItem()
    .setTitle('About you')
    .setHelpText(
      'These questions let us check whether you match the segment we designed for. ' +
      'Please answer all of them — blank answers made the last screener unusable.'
    );

  form.addMultipleChoiceItem()
    .setTitle('Your age')
    .setChoiceValues(['18–23', '24–30', '31–35', '36 or older'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Where do you live?')
    .setChoiceValues([
      'Tier 1 city (e.g. Mumbai, Delhi NCR, Bengaluru, Hyderabad, Chennai, Kolkata, Pune)',
      'Tier 2 city',
      'Tier 3 or smaller town',
      'Outside India'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Roughly how many items are on your fashion wishlist right now?')
    .setChoiceValues(['1–4', '5–10', '11–25', 'More than 25'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Do you have several wishlist items that have been sitting there for 2+ weeks?')
    .setChoiceValues(['Yes, several', 'Yes, one or two', 'No — most were saved recently', 'Not sure'])
    .setRequired(true);

  // --- Diagnostic: WPCR-positive is allowed, but is not the interview item ---
  var sWpcr = form.addPageBreakItem()
    .setTitle('Recent purchases (for context)')
    .setHelpText(
      'Either answer is fine. The next pages are still about an item you have NOT bought.'
    );

  form.addMultipleChoiceItem()
    .setTitle(
      'In the last 30 days, did you purchase at least one item that had been on your ' +
      'wishlist before you bought it?'
    )
    .setChoiceValues(['Yes', 'No'])
    .setRequired(true);

  // --- The frozen item ---
  var sItem = form.addPageBreakItem()
    .setTitle('The item that is still sitting there')
    .setHelpText(
      'Pick ONE item you saved and have not purchased. Prefer ethnic, occasion, or ' +
      'fashion-forward clothing if you have one. Every question below is about that item.'
    );

  form.addParagraphTextItem()
    .setTitle('What is the item? (brand + product type + occasion if relevant)')
    .setHelpText('e.g. Libas peach anarkali for a family function; wine sequin gown for a wedding guest')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('What kind of item is this?')
    .setChoiceValues([
      'Ethnic / occasion wear',
      'Fashion-forward / western (not basics)',
      'Basics / everyday',
      'Footwear or accessories',
      'Other'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('How long has this item been on your wishlist?')
    .setChoiceValues([
      'Less than 7 days',
      '7–14 days',
      '15–21 days',
      '22–30 days',
      'More than 30 days'
    ])
    .setRequired(true);

  // --- Why saved ---
  form.addPageBreakItem()
    .setTitle('Why you saved it')
    .setHelpText('Same item as above.');

  form.addCheckboxItem()
    .setTitle('Why did you save this item to your wishlist? (Select all that apply)')
    .setChoiceValues([
      'I liked how it looked',
      'Saving it for a specific occasion',
      'Wanted to think it over before spending',
      'Comparing it with other options on my wishlist',
      "Wasn't sure if I needed it yet",
      'Waiting for the price to drop',
      'Mostly bookmarking — no real plan to buy'
    ])
    .showOtherOption(true)
    .setRequired(true);

  // --- Intent: then vs now ---
  form.addPageBreakItem()
    .setTitle('Do you still intend to buy it?')
    .setHelpText('Same item.');

  form.addMultipleChoiceItem()
    .setTitle('When you first saved it, did you intend to buy it eventually?')
    .setChoiceValues([
      'Yes, definitely',
      'Probably',
      'Not sure',
      'No — mostly bookmarking'
    ])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Do you still intend to purchase THIS item?')
    .setChoiceValues([
      'Yes, definitely',
      'Probably — still have some doubt',
      'Not sure — might drop it',
      'No — it is just sitting there / I have moved on'
    ])
    .setRequired(true);

  // --- What is stopping them now ---
  form.addPageBreakItem()
    .setTitle('What is stopping you')
    .setHelpText('Think about right now, not what might have stopped you in the past.');

  form.addMultipleChoiceItem()
    .setTitle('What is the MAIN thing stopping you from buying it now? (Select one)')
    .setChoiceValues([
      "Not sure it'll fit me",
      'Not sure about quality (fabric, threadwork, photo vs real product)',
      'Comparing it with similar items on my wishlist or other apps',
      'Not sure it suits the occasion or my style',
      'Waiting for a better price or salary',
      'Just keep putting it off — no single reason'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Anything else that adds to your hesitation?')
    .setRequired(false);

  // --- What would make them buy + info still needed ---
  form.addPageBreakItem()
    .setTitle('What would unstick you')
    .setHelpText('Same item. This is about the next 30 days, not a past purchase.');

  form.addCheckboxItem()
    .setTitle(
      'What would make you purchase this item in the next 30 days? (Select all that apply)'
    )
    .setChoiceValues([
      'Reviews or photos from buyers similar to me (height, size, occasion)',
      'A clearer answer on fit / sizing (e.g. runs small, true to size)',
      'Confirmation the fabric / threadwork looks like the photo',
      'Confirmation it suits the occasion I have in mind',
      'Finishing a comparison against 2–3 saved alternatives',
      'Friend or family validation',
      'An event deadline I cannot keep waiting on',
      'A better price (we cannot offer this — still tell us if it is the real gate)'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('What specific information do you still need before you would decide yes or no?')
    .setHelpText(
      'e.g. real fabric feel, embroidery quality, fit for your size, occasion appropriateness'
    )
    .setRequired(true);

  // --- Alternatives ---
  form.addMultipleChoiceItem()
    .setTitle('Are you considering buying something else instead of this exact item?')
    .setChoiceValues([
      'Yes — another item on my wishlist (same app)',
      'Yes — something on a different app or store',
      'No — it is this item or nothing',
      "Haven't seriously compared alternatives"
    ])
    .setRequired(true);

  // --- Outside the app ---
  form.addPageBreakItem()
    .setTitle('Outside the app')
    .setHelpText('Same item.');

  form.addCheckboxItem()
    .setTitle(
      'Have you done anything outside the shopping app while deciding on this item? ' +
      '(Select all that apply)'
    )
    .setChoiceValues([
      'Searched reviews on Google or YouTube',
      'Asked a friend or family member',
      'Checked Instagram or influencers for styling / real photos',
      'Compared prices on other sites',
      'Visited a physical store to check fit or quality',
      'Nothing — I have only looked at it inside the app'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('How do you currently deal with the uncertainty, if at all?')
    .setHelpText(
      'e.g. would order two sizes and return one; wait for payday; ask a friend on WhatsApp; ' +
      'just leave it in the wishlist'
    )
    .setRequired(true);

  // --- MVP probe ---
  form.addPageBreakItem()
    .setTitle('Fit & Confidence Assistant (concept)')
    .setHelpText(
      'Imagine an in-app layer on the wishlist: review-backed answers on fit, quality ' +
      '(fabric/threadwork vs photo), occasion-fit, and comparing 2–3 saved items. No discounts.'
    );

  form.addMultipleChoiceItem()
    .setTitle(
      'If this assistant were on your wishlist for this item, would it help you decide ' +
      'yes or no faster?'
    )
    .setChoiceValues([
      'Yes — I could decide sooner (buy or drop it)',
      'Maybe — I would still need to try it on or see it in person',
      'No — price or something else is the real blocker'
    ])
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('What would you ask the assistant about this item? (optional)')
    .setHelpText('e.g. Will embroidery look cheap? Should I size up? Good for a daytime wedding?')
    .setRequired(false);

  // --- Optional live interview ---
  form.addPageBreakItem().setTitle('Optional follow-up');

  var qFollow = form.addMultipleChoiceItem()
    .setTitle(
      'Open to a 15–20 min follow-up chat about this saved item? (Casual, no sales pitch.)'
    )
    .setRequired(true);

  var sContact = form.addPageBreakItem().setTitle('Contact');

  form.addTextItem()
    .setTitle('Email or phone (only if you said yes above)')
    .setRequired(false);

  qFreq.setChoices([
    qFreq.createChoice('Weekly', sUnsold),
    qFreq.createChoice('2–4 times a month', sUnsold),
    qFreq.createChoice('Once a month', sUnsold),
    qFreq.createChoice('Rarely', sExit)
  ]);

  qUnsold.setChoices([
    qUnsold.createChoice('Yes — I have at least one unsold saved item', sAbout),
    qUnsold.createChoice('No — everything I saved, I already bought or deleted', sExit)
  ]);

  qFollow.setChoices([
    qFollow.createChoice('Yes — happy to chat', sContact),
    qFollow.createChoice('No thanks', FormApp.PageNavigationType.SUBMIT)
  ]);
}
