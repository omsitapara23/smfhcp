$("#generalPostTagsAddButton").click(function(){
    $("#generalPostTagsWrapper").append("<div class=\"input-group\" style=\"margin-top: 10px;\">" +
                    "<input name=\"generalPostTags[]\" type=\"text\" required=\"true\" class=\"form-control\">" +
                    "<span class=\"input-group-btn\">" +
                        "<button class=\"btn btn-success btn-remove plus-minus\" type=\"button\">" +
                            "<i class=\"fa fa-minus\"></i>" +
                        "</button>" +
                    "</span>" +
                "</div>");
});

$("#general-post-form").on('submit', function(event){
    event.preventDefault();
    console.log("general post form submitted!")
    generalPost();
});

function generalPost() {
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
    var tags = []
    $('input[name="generalPostTags[]"]').each(function() {
        tags.push($(this).val());
    });
    $.ajax({
        url : "/create_post/general_post/",
        type : "POST",
        data : { title : $('#generalPostTitle').val(), description : $('#generalPostDesc').val(),
                tags : JSON.stringify({ 'tags': tags })
        },
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
        success : function(json) {
            if (json.redirect) {
                window.location.href = json.redirect_url;
            }
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        }
    });
}
