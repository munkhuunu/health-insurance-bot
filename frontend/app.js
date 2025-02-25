(function () {
    'use strict';

    angular
        .module('core', [])
        .controller('AppController', AppController);

    AppController.$inject = ['$http', '$scope', '$timeout'];

    function AppController($http, $scope, $timeout) {
        var vm = this;

        vm.messages = [];
        vm.userMessage = '';
        vm.loading = false;
        vm.lastBotMessage = '';
        vm.isDarkMode = true; // Default to dark mode

        // Initial bot message with quick replies
        vm.messages.push({
            text: "Сайн байна уу? Эрүүл мэндийн даатгалын талаар танд ямар мэдээлэл хэрэгтэй байна вэ?",
            sender: "bot",
            quickReplies: ["Эрүүл мэндийн даатгалтай гэрээт эмнэлгүүд?", "Эрүүл мэндийн даатгалын шимтгэл төлөлтийн талаар?", "ЭМД-р хөнгөлөлттэй авч болох эмийн талаар?", "ЭМД-р хөнгөлөх тусламж, үйлчилгээнүүд?", "Эрүүл мэндийн даатгал гэж юу вэ?"]
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
            vm.messages.push(message);
            var index = 0;

            function typeNextLetter() {
                if (index < botResponse.length) {
                    message.text += botResponse.charAt(index);
                    index++;
                    $timeout(typeNextLetter, 50);
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
                vm.messages.push({ text: vm.userMessage, sender: "user" });
                vm.userMessage = '';
                typeMessage(invalidMessage);
                return;
            }

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

        vm.sendQuickReply = function(reply) {
            vm.userMessage = reply;
            vm.sendMessage();
        };

        vm.startVoiceInput = function() {
            // Simulate voice input (placeholder—replace with actual voice recognition logic)
            var voiceMessage = "Хоолойн тусламжаар илгээгдсэн мессеж";
            vm.userMessage = voiceMessage;
            vm.sendMessage();
            alert("Хоолойн тусламжаар мессеж илгээх боломж идэвхжсэн. (Симуляц) Дараа нь жинхэнэ API-г холбоно уу.");
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

        scrollToBottom();
    }
})();