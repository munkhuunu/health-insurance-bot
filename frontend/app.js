(function () {
    'use strict';

    angular
        .module('core', [])
        .controller('AppController', AppController);

    AppController.$inject = ['$http', '$scope', '$timeout', '$window'];

    function AppController($http, $scope, $timeout, $window) {
        var vm = this;

        vm.messages = [];
        vm.userMessage = '';
        vm.loading = false;
        vm.lastBotMessage = '';
        vm.isDarkMode = true; // Default to dark mode (like Egene VQA)

        // Initial bot message with quick replies matching NLU examples
        vm.messages.push({
            text: "Сайн байна уу? Би яаж туслах вэ?",
            sender: "bot",
            quickReplies: [
                "ЭМД төлбөрөө хаанаас төлөх вэ?",
                "Ямар эмнэлгүүд ЭМД-тэй гэрээтэй вэ?"
            ]
        });

        // Apply dark mode by default
        document.body.classList.add('dark-mode');

        function scrollToBottom() {
            $timeout(function () {
                var chatBox = document.getElementById("chat-box");
                if (chatBox) {
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            }, 100);
        }

        function typeMessage(botResponse) {
            if (!botResponse || !botResponse.trim() || botResponse === "-") return;

            var message = { text: "", sender: "bot" };
            vm.messages.push(message); // Add bot response to chat messages, not input
            var index = 0;

            function typeNextLetter() {
                if (index < botResponse.length) {
                    message.text += botResponse.charAt(index);
                    index++;
                    $timeout(typeNextLetter, 25); /* Faster typing for full desktop */
                }
                $scope.$apply();
                scrollToBottom();
            }

            typeNextLetter();
        }

        vm.sendMessage = function () {
            if (!vm.userMessage || vm.userMessage.trim() === "") return;

            if (!/^[а-яА-ЯөӨүҮёЁ0-9\s.,!?@#$%^&*()_+=<>:;"'{}\[\]\\\/-]+$/.test(vm.userMessage)) {
                var invalidMessage = "Би зөвхөн монгол хэлээр ойлгох тул та асуултаа кирилл үсгээр бичнэ үү.";
                vm.messages.push({ text: vm.userMessage, sender: "user" }); // Add user message to chat
                vm.userMessage = '';
                typeMessage(invalidMessage);
                return;
            }

            vm.messages.push({ text: vm.userMessage, sender: "user" }); // Add user message to chat, not input
            scrollToBottom();
            vm.loading = true;

            $http.post("http://127.0.0.1:5000/chat", { message: vm.userMessage }, {
                headers: {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*" // Add CORS header to allow all origins
                }
            })
            .then(function (response) {
                $timeout(function () {
                    console.log("✅ Success! Response from API:", response.data);
            
                    var botResponse = response.data.text || response.data.response?.[0] || "❌ Алдаа: Rasa хариу илгээсэнгүй.";
                    
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
                }, 700);
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
                } else if (error.status === 404) {
                    errorMessage = "❌ /webhook эндпоинт олдсонгүй! Раса-гийн actions server-г шалгана уу.";
                }

                $timeout(function () {
                    typeMessage(errorMessage); // Add error message to chat, not input
                    vm.loading = false;
                }, 500);
            });

            vm.userMessage = ''; // Clear input after sending, ensure bot response stays in chat
        };

        vm.sendQuickReply = function(reply) {
            vm.userMessage = reply;
            vm.sendMessage();
        };

        vm.startVoiceInput = function() {
            // Real voice input using Web Speech API
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'mn-MN'; // Mongolian language
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onresult = function(event) {
                const voiceMessage = event.results[0][0].transcript;
                vm.userMessage = voiceMessage;
                vm.sendMessage();
                $scope.$apply();
            };

            recognition.onerror = function(event) {
                console.error("Voice recognition error:", event.error);
                typeMessage("❌ Хоолойн тусламжтай алдаа гарлаа. Дахин оролдоно уу.");
            };

            recognition.start();
            typeMessage("Хоолойн тусламж идэвхжлээ. Яриагаа эхлүүлнэ үү...");
        };

        vm.toggleTheme = function () {
            vm.isDarkMode = !vm.isDarkMode; // Toggle mode
        
            if (vm.isDarkMode) {
                document.body.classList.add("dark-mode");
                document.body.classList.remove("light-mode");
            } else {
                document.body.classList.add("light-mode");
                document.body.classList.remove("dark-mode");
            }
        };

        // Adjust container size dynamically based on window size
        function adjustContainerSize() {
            const container = document.querySelector('.chat-container');
            const width = $window.innerWidth * 0.9; // 90% of viewport width
            const height = $window.innerHeight * 0.8; // 80% of viewport height for Egene VQA
            container.style.width = `${Math.min(width, 1000)}px`; // Limit max width to match Egene VQA
            container.style.height = `${Math.min(height, 800)}px`; // Limit max height to match Egene VQA
        }

        angular.element($window).on('resize', function() {
            $scope.$apply(adjustContainerSize);
        });

        // Initial size adjustment
        adjustContainerSize();
        scrollToBottom();
    }
})();