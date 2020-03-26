function checkValidity() {
    $('#msgDivReset').html('')
    $('#msgDivReset').removeClass("alert alert-danger")
    var password = $("#newPasswordId").val();
    var confirmPassword = $("#confirmNewPasswordId").val();
    if (password != confirmPassword) {
        $('#msgDivReset').addClass("alert alert-danger").html("Password and Confirm password do not match.");
        console.log("password wrong");
        return false;
    }
    return true;
}

$('#resetPasswordForm').on('submit', function(event){
    console.log("reset form submitted!")
    if(checkValidity()) {
        console.log("proceeded to website")
    } else {
        event.preventDefault();
    }
});
