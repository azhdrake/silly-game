$(document).on('submit', '#new-card-form', function(event){
    event.preventDefault();
    let serializedData = $(this).serialize();
    console.log("form submitted!");
    create_card(serializedData);
});

function create_card(cleanData) {
    $.ajax({
        url:"{% url 'create_card' %}",
        type: "POST",
        data: { cleanData },

        success: function(response){
            $("#new-card-form").trigger('reset')
            $('#card-text').focus();
            console.log("my god it worked");
        },

        error: function(response){
            alert(response["responseText"]);
        }
    })
};

//readyState,getResponseHeader,getAllResponseHeaders,setRequestHeader,overrideMimeType,statusCode,abort,state,always,catch,pipe,then,promise,progress,done,fail,responseText,status,statusText