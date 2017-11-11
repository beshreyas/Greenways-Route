$(document).ready(function(){

  var mc = {
    '0-19'     : 'red',
    '20-59'    : 'orange',
    '60-100'   : 'green'
  };

function between(x, min, max) {
  return x >= min && x <= max;
}



  var dc;
  var first;
  var second;
  var th;

  $('p').each(function(index){

    th = $(this);

    dc = parseInt($(this).attr('data-color'),10);


      $.each(mc, function(name, value){


        first = parseInt(name.split('-')[0],10);
        second = parseInt(name.split('-')[1],10);

        console.log(between(dc, first, second));

        if( between(dc, first, second) ){
          th.addClass(value);
        }



      });

  });
});