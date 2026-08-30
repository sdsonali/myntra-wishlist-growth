function myFunction() {
  var form = FormApp.create('Wishlist shopping decisions');
  form.setProgressBar(true);
  form.setShowLinkToRespondAgain(false);
  form.setAllowResponseEdits(false);
  form.setDescription(
    'Takes about 3–4 minutes. We will ask about one specific item currently sitting in your wishlist — not shopping in general.\n\n' +
    'There is no sales pitch. This helps us understand how people decide whether to buy saved items.'
  );

  var q1 = form.addMultipleChoiceItem()
    .setTitle('How often do you shop for fashion/clothing online?')
    .setRequired(true);

  var sQ2 = form.addPageBreakItem().setTitle('Your wishlist');

  var q2 = form.addMultipleChoiceItem()
    .setTitle('Roughly how many items are currently in your wishlist across shopping apps?')
    .setRequired(true);

  var sQ3 = form.addPageBreakItem().setTitle('Older saved items');

  var q3 = form.addMultipleChoiceItem()
    .setTitle("Do you have anything in your wishlist that you added 2+ weeks ago and still haven't purchased?")
    .setRequired(true);

  var sExit = form.addPageBreakItem()
    .setTitle('Thanks for your time')
    .setHelpText(
      'This survey is for people who shop for fashion online at least once a month, ' +
      'have 10+ items in a wishlist, and still have something they saved 2+ weeks ago. ' +
      "You're not in that group right now — no further questions."
    );
  sExit.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  var sMain = form.addPageBreakItem()
    .setTitle('One specific item')
    .setHelpText(
      'Pick ONE item currently sitting in your wishlist. Every question after this is about that same item — not wishlists in general.'
    );

  form.addParagraphTextItem()
    .setTitle('Think of ONE specific item currently sitting in your wishlist. What is it?')
    .setHelpText('e.g. a kurta, sneakers, a dress for a wedding')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Roughly how long ago did you add it to your wishlist?')
    .setChoiceValues(['Less than a week', '1-2 weeks', '2-4 weeks', '1 month+'])
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('Why you saved it')
    .setHelpText('Still thinking about the same item you just named.');

  form.addCheckboxItem()
    .setTitle('Why did you save this item to your wishlist? (Select all that apply)')
    .setChoiceValues([
      'I liked how it looked',
      'Waiting for the price to drop',
      "Wasn't sure if I needed it",
      'Wanted to think it over',
      'Saving it for a specific occasion',
      'Comparing it with other options'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('Do you still want it?')
    .setHelpText('Same item as before.');

  form.addMultipleChoiceItem()
    .setTitle('Do you still intend to buy it?')
    .setChoiceValues(['Yes, definitely', 'Probably', 'Not sure anymore', "No, I've lost interest"])
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle("What's stopping you")
    .setHelpText('Same item as before.');

  form.addMultipleChoiceItem()
    .setTitle('What is the MAIN thing stopping you from buying it right now? (Select one)')
    .setChoiceValues([
      "Not sure it'll fit me",
      'Not sure about the quality',
      'Comparing it with similar items elsewhere',
      'Waiting for a better price',
      "Just haven't gotten around to it",
      'Not sure it suits the occasion/my style'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Is there anything else adding to your hesitation, beyond the main reason above?')
    .setRequired(false);

  form.addPageBreakItem()
    .setTitle('What would resolve it')
    .setHelpText('Same item as before.');

  form.addCheckboxItem()
    .setTitle('What would make you go ahead and buy it? (Select all that apply)')
    .setChoiceValues([
      'More reviews/photos from real buyers similar to me',
      "A clearer idea of how it'll fit",
      'Confirmation it suits the occasion I have in mind',
      'Comparing it directly with alternatives',
      'Seeing someone I trust wear/recommend it',
      "Nothing — I've decided not to buy it"
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('What specific information do you wish you had before deciding?')
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('Alternatives')
    .setHelpText('Same item as before.');

  form.addMultipleChoiceItem()
    .setTitle('Are you considering buying something else instead of this exact item?')
    .setChoiceValues([
      'Yes, a similar item on the same app',
      'Yes, something from a different app/store',
      "No, it's this item or nothing",
      "Haven't thought about alternatives"
    ])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Before deciding on an item like this, do you do anything outside the app? (Select all that apply)')
    .setChoiceValues([
      'Search for reviews on Google/YouTube',
      'Ask a friend or family member',
      'Check Instagram/influencers for styling ideas',
      'Compare prices on other sites',
      'Visit a physical store',
      'Nothing, I decide within the app'
    ])
    .showOtherOption(true)
    .setRequired(true);

  form.addPageBreakItem()
    .setTitle('How you deal with uncertainty')
    .setHelpText('Same item as before.');

  form.addParagraphTextItem()
    .setTitle('How do you currently deal with this kind of uncertainty, if at all?')
    .setHelpText('e.g. I just order 2 sizes and return one; I wait and see if reviews improve; I ask friends')
    .setRequired(true);

  form.addPageBreakItem().setTitle('Optional follow-up');

  var q15 = form.addMultipleChoiceItem()
    .setTitle(
      'Would you be open to a quick 15-20 min chat about your shopping habits? (We will keep it casual, no sales pitch.)'
    )
    .setRequired(true);

  var sContact = form.addPageBreakItem().setTitle('How can we reach you?');

  form.addTextItem()
    .setTitle('Email or phone number')
    .setRequired(true);

  q1.setChoices([
    q1.createChoice('Weekly', sQ2),
    q1.createChoice('2-4 times a month', sQ2),
    q1.createChoice('Once a month', sQ2),
    q1.createChoice('Rarely', sExit)
  ]);

  q2.setChoices([
    q2.createChoice('Less than 5', sExit),
    q2.createChoice('5-10', sExit),
    q2.createChoice('10+', sQ3)
  ]);

  q3.setChoices([
    q3.createChoice('Yes', sMain),
    q3.createChoice('No', sExit)
  ]);

  q15.setChoices([
    q15.createChoice('Yes — please share your email/phone', sContact),
    q15.createChoice('No thanks', FormApp.PageNavigationType.SUBMIT)
  ]);

  Logger.log('Live form: ' + form.getPublishedUrl());
  Logger.log('Edit form: ' + form.getEditUrl());
}
