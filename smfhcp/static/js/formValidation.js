function Validate() {
    var errorDiv = document.getElementById("errorDiv");
    errorDiv.innerHTML = ""
    errorDiv.style.display = "none";
    var nameRegex = /^[a-zA-Z_]+$/;
    var validUsername = document.getElementById("exampleInputUsername1").value.match(nameRegex);
    if(validUsername == null){
        var content = document.createTextNode("Your user name is not valid. Only characters A-Z, a-z and '_' are acceptable.");
        errorDiv.classList.add("alert");
        errorDiv.classList.add("alert-danger");
        errorDiv.appendChild(content);
        errorDiv.style.display = "block";
        return false;
    }

    var password = document.getElementById("txtPassword").value;
    var confirmPassword = document.getElementById("txtConfirmPassword").value;
    if (password != confirmPassword) {
        var content = document.createTextNode("Password and Confirm password do not match.");
        errorDiv.classList.add("alert");
        errorDiv.classList.add("alert-danger");
        errorDiv.appendChild(content);
        errorDiv.style.display = "block";
        return false;
    }
    return true;
}