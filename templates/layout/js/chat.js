

$(function(){
	$('.chat').chat();
})

$.fn.chat = function(){
	var username = 'Херка';
	var botname = 'Боженька';
	var url = 'НЕТ ПУТИ';
	var widget = this;
	var screen = $('.screen');
	var input = $('.input textarea');
	var button = $('.input button');
	
	button.click(say);
	
	input.keypress(function(e){
		if (e.which == 13) {
			console.log('enter pressed');
			say();
			return false;
		}
	});
	

	function say(e) {
		var q = input.val();
		writePhrase(q, false);
		input.val('');

		/*
		$.get(url, function(answer){
			writePhrase(answer, true);
		})
		*/
		
		

		
	}

	function writePhrase(phrase, isBot){
		
		var div = $('<div class="item"><span class="name"></span><span class="content"></span></div>')
			.appendTo(screen);
		
		$('.content', div).text(phrase);		

		if (isBot) {
			div.addClass('bot');
			$('.name', div).text(username + ':');
		
		} else {
			div.addClass('user');
			$('.name', div).text(username + ':');
			
		}
	
	}
	
}