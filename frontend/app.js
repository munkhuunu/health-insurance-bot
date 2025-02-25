(function () {
    'use strict';

    angular
        .module('core', [])
        .controller('AppController', AppController);

    AppController.$inject = ['$http', '$location', '$scope', '$rootScope', '$timeout', '$anchorScroll', '$window'];

    function AppController($http, $location, $scope, $rootScope, $timeout, $anchorScroll, $window) {
        var vm = this;

        vm.messages = [];
        vm.userMessage = '';
        vm.loading = false;
        vm.lastBotMessage = ''; // Store last bot response to prevent duplicates
        vm.messages.push({ text: "Сайн байна уу? Эрүүл мэндийн даатгалын талаар танд ямар мэдээлэл хэрэгтэй байна вэ?", sender: "bot" });
        vm.isDarkMode = true; // Default to dark mode

        // Scroll to bottom after new message
        function scrollToBottom() {
            $timeout(function () {
                var chatBox = document.getElementById("chat-box");
                if (chatBox) {
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            }, 100);
        }

        // Typing effect for chatbot response
        function typeMessage(botResponse) {
            if (!botResponse || !botResponse.trim() || botResponse === "-") return;

            var message = { text: "", sender: "bot" };
            vm.messages.push(message);
            var index = 0;

            function typeNextLetter() {
                if (index < botResponse.length) {
                    message.text += botResponse.charAt(index);
                    index++;
                    $timeout(typeNextLetter, 50);
                }
                $scope.$apply(); // Ensure Angular updates the view
                scrollToBottom();
            }

            typeNextLetter();
        }

        // Send message and get chatbot response
        vm.sendMessage = function () {
            if (!vm.userMessage || vm.userMessage.trim() === "") return;

            // Allow Cyrillic, numbers, and extra symbols
            if (!/^[а-яА-ЯөӨүҮёЁ0-9\s.,!?@#$%^&*()_+=<>:;"'{}\[\]\\\/-]+$/.test(vm.userMessage)) {
                var invalidMessage = "Би зөвхөн монгол хэлээр ойлгох тул та асуултаа кирилл үсгээр бичнэ үү.";
                vm.messages.push({ text: vm.userMessage, sender: "user" });
                vm.userMessage = '';
                typeMessage(invalidMessage);
                return;
            }

            // Add user message to chat
            vm.messages.push({ text: vm.userMessage, sender: "user" });
            scrollToBottom();
            vm.loading = true;

            $http.post("http://localhost:5000/chat", { message: vm.userMessage }, {
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(function (response) {
                $timeout(function () {
                    console.log("✅ Success! Response from backend:", response.data);

                    var botResponse = response.data && response.data.response 
                        ? response.data.response.join(" ").normalize()
                        : "❌ Алдаа: rasa хариу илгээсэнгүй. Дахин оролдоно уу.";
                    
                    if (!botResponse.trim()) {
                        console.warn("⚠️ Empty response detected. Using fallback message.");
                        botResponse = "Уучлаарай, би энэ асуултад хариулж чадахгүй байна.";
                    }
            
                    if (vm.lastBotMessage === botResponse) {
                        console.warn("⚠️ Duplicate bot response detected. Skipping...");
                        vm.loading = false;
                        return;
                    }
                    vm.lastBotMessage = botResponse;

                    typeMessage(botResponse);
                    vm.loading = false;
                }, 1000);
            })
            .catch(function (error) {
                console.error("❌ Error:", error);

                var errorMessage = "❌ Алдаа гарлаа! Интернет холболтоо шалгана уу.";
                if (error.status === 0) {
                    errorMessage = "❌ Сервер ажиллахгүй байна. Дахин оролдоно уу.";
                } else if (error.status === 500) {
                    errorMessage = "❌ Серверийн алдаа! Дахин оролдоно уу.";
                } else if (error.data && error.data.message) {
                    errorMessage = "❌ " + error.data.message;
                }

                $timeout(function () {
                    typeMessage(errorMessage);
                    vm.loading = false;
                }, 500);
            });

            vm.userMessage = '';
        };

        // Adjust textarea height dynamically
        vm.adjustTextarea = function() {
            var textarea = document.querySelector(".chat-input");
            if (textarea) {
                textarea.style.height = "auto"; // Reset height
                textarea.style.height = textarea.scrollHeight + "px"; // Set to content height
            }
        };

        // Initial scroll to bottom
        scrollToBottom();

        // Theme toggle function
        vm.toggleTheme = function() {
            if (vm.isDarkMode) {
                document.body.classList.remove('dark-mode');
                document.body.classList.add('light-mode');
            } else {
                document.body.classList.remove('light-mode');
                document.body.classList.add('dark-mode');
            }
        };
    }
})();