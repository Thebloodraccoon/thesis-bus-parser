<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const home = ref(null);
const meet = ref(null);
const features = ref(null);
const pricing = ref(null);
const router = useRouter();

function goHome() {
    router.push('/');
}

function scrollToElement($element) {
    setTimeout(() => {
        $element.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
    }, 200);
}
</script>

<template>
    <div ref="home" class="landing-container" style="background: #100e23">
        <div id="header" class="landing-header flex flex-col w-full p-12" style="min-height: 1000px; background: url('/demo/images/landing/landing-header-2x.jpg') top left no-repeat; background-size: cover">
            <div class="header-menu-container flex items-center justify-between">
                <div class="header-left-elements flex items-center justify-between">
                    <div class="layout-topbar-logo flex items-center cursor-pointer" @click="goHome">
                        <img src="/layout/images/logo/logo-dark.png" alt="layout" class="logo" style="height: 32px" />
                        <img src="/layout/images/logo/appname-dark.png" alt="layout" class="appname ml-2" style="height: 12px" />
                    </div>

                    <ul ref="menu" id="menu" style="top: 0px; right: 0%" class="list-none !hidden lg:!flex lg:!flex-row !flex-col !items-start absolute lg:relative h-screen lg:h-auto m-0 z-50 w-full sm:w-6/12 lg:w-full lg:py-0 pl-8">
                        <a
                            class="cursor-pointer !block lg:!hidden text-gray-800 font-medium leading-normal hover:text-gray-800 absolute"
                            style="top: 3rem; right: 2rem"
                            v-styleclass="{ selector: '@parent', enterFromClass: '!hidden', enterActiveClass: 'animate-scalein', leaveToClass: '!hidden', leaveActiveClass: 'animate-fadeout' }"
                        >
                            <i class="pi pi-times !text-4xl"></i>
                        </a>

                        <li class="mt-8 lg:mt-0">
                            <a
                                @click="scrollToElement(home)"
                                v-styleclass="{ selector: '@grandparent', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden' }"
                                class="flex m-0 lg:ml-8 lg:px-0 px-4 py-4 text-gray-800 font-medium leading-normal hover:text-gray-800 cursor-pointer"
                            >
                                <span>Home</span>
                            </a>
                        </li>
                        <li>
                            <a
                                @click="scrollToElement(meet)"
                                v-styleclass="{ selector: '@grandparent', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden' }"
                                class="flex m-0 lg:ml-8 lg:px-0 px-4 py-4 text-gray-800 font-medium leading-normal hover:text-gray-800 cursor-pointer"
                            >
                                <span>Meet Atlantis</span>
                            </a>
                        </li>
                        <li>
                            <a
                                @click="scrollToElement(features)"
                                v-styleclass="{ selector: '@grandparent', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden' }"
                                class="flex m-0 lg:ml-8 lg:px-0 px-4 py-4 text-gray-800 font-medium leading-normal hover:text-gray-800 cursor-pointer"
                            >
                                <span>Features</span>
                            </a>
                        </li>
                        <li>
                            <a
                                @click="scrollToElement(pricing)"
                                v-styleclass="{ selector: '@grandparent', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden' }"
                                class="flex m-0 md:ml-8 md:px-0 px-4 py-4 text-gray-800 font-medium leading-normal hover:text-gray-800 cursor-pointer"
                            >
                                <span>Pricing</span>
                            </a>
                        </li>
                        <li>
                            <a
                                v-styleclass="{ selector: '@grandparent', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden' }"
                                class="flex m-0 md:ml-8 md:px-0 px-4 py-4 text-gray-800 font-medium leading-normal hover:text-gray-800 cursor-pointer"
                            >
                                <span>Buy Now</span>
                            </a>
                        </li>
                    </ul>
                </div>

                <div class="header-right-elements flex items-center justify-between">
                    <a class="contact-icons font-medium text-gray-700 cursor-pointer">
                        <i class="pi pi-github text-gray-700 hover:text-gray-900 mr-4 text-xl"></i>
                    </a>

                    <a class="contact-icons font-medium text-gray-700 cursor-pointer">
                        <i class="pi pi-twitter text-gray-700 hover:text-gray-900 mr-4 text-xl"></i>
                    </a>

                    <Button class="contact-button mr-4" severity="secondary" outlined text style="background: rgba(68, 72, 109, 0.05)">
                        <span class="p-button-label !text-gray-700 !font-semibold">Contact</span>
                    </Button>

                    <a
                        class="lg:hidden font-medium text-gray-700 cursor-pointer"
                        v-styleclass="{ selector: '#menu', enterFromClass: '!hidden', enterActiveClass: 'animate-fadein', leaveToClass: '!hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: 'true' }"
                    >
                        <i class="pi pi-bars fs-xlarge"></i>
                    </a>
                </div>
            </div>

            <div class="header-text" style="padding: 100px 60px">
                <h1 class="mb-0 text-gray-800 font-semibold" style="font-size: 80px; line-height: 95px">This is Atlantis</h1>
                <h2 class="mt-0 font-medium text-4xl text-gray-700 mb-4">Modern, fresh and groovy</h2>
                <a href="/" class="p-button !bg-cyan-500 !border-cyan-500 font-bold rounded" style="mix-blend-mode: multiply; padding: 0.858rem 1.142rem">
                    <span class="p-button-text !text-gray-700">Live Demo</span>
                </a>
            </div>

            <div ref="features" class="header-features" style="padding: 100px 60px">
                <div class="grid grid-cols-12 gap-4 flex">
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Responsive Layout</span>
                            <span class="content">View it on the web and mobile device. Prime premium themes are aready for the all devices.</span>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Fresh</span>
                            <span class="content">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.</span>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Modern Design</span>
                            <span class="content">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor.</span>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Clean code</span>
                            <span class="content">Our frontend is so easy to understand. If you want to modify the code it’s an easy job for you. Our code is clean and easy to read.</span>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Ready!</span>
                            <span class="content">We work hard to write down all aspects of prime themes to make sure that there is no unanswered questions left.</span>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-6 lg:col-span-4 flex justify-center">
                        <div class="header-feature-box mr-4 mb-6 rounded-3xl p-8 text-white">
                            <span class="title mb-4 block text-2xl">Well documented</span>
                            <span class="content">We work hard to write down all aspects of prime themes to make sure that there is no unanswered questions left.</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div ref="meet" id="meet-atlantis" class="flex justify-center w-full bg-gray-900 relative" style="min-height: 620px; padding-top: 65px">
            <div class="ellipsis-1 absolute right-0" style="z-index: 11">
                <img src="/demo/images/landing/ellipse-1.png" alt="atlantis" width="410" />
            </div>
            <div class="ellipsis-2 absolute left-0" style="z-index: 11; bottom: -100px">
                <img src="/demo/images/landing/ellipse-2.png" alt="atlantis" width="420" />
            </div>
            <div class="ellipsis-3 absolute" style="z-index: 11; filter: blur(20px); left: 130px; top: 40px">
                <img src="/demo/images/landing/ellipse-3.png" alt="atlantis" width="300" />
            </div>
            <div class="ellipsis-4 absolute bottom-0" style="z-index: 9; right: 310px">
                <img src="/demo/images/landing/ellipse-4.png" alt="atlantis" width="125" />
            </div>

            <div class="atlantis-modes w-auto px-8" style="z-index: 10">
                <img src="/demo/images/landing/atlantis-dark.png" alt="atlantis" class="w-full" style="max-width: 800px; border-radius: 8px" />
            </div>
        </div>

        <div class="clip-background bg-gray-900 relative">
            <div class="landing-wrapper clip-path !px-12 !pb-20 absolute w-full" style="color: #44486d; background: linear-gradient(180deg, #f4f8fb 17.13%, #eeeefa 65.89%)">
                <div id="features" class="pr-20 features" style="padding-left: 14rem">
                    <h2 class="font-medium text-3xl text-center text-gray-800 mb-4">Features</h2>
                    <div class="grid grid-cols-12 gap-4 feature-boxes feature-boxes-1" style="margin-bottom: 170px">
                        <div class="col-span-12 md:col-span-6">
                            <h3 class="font-medium text-3xl mb-4">Curabitur ullamcorper molesti</h3>
                            <p class="text-xl" style="max-width: 420px">
                                Ut eget ante id libero scelerisque sagittis. Aliquam porta quam at eros ornare, nec volutpat purus ornare. Curabitur vestibulum pharetra dui, feugiat venenatis augue accumsan in. Fusce ullamcorper efficitur dui
                                vestibulum imperdiet. Morbi rhoncus commodo est, vel molestie sapien dapibus et. Nam a blandit urna. Maecenas porttitor et neque eu vehicula. Nunc dictum posuere elementum.
                            </p>
                        </div>
                        <div class="col-span-12 md:col-span-6 flex flex-col">
                            <div class="widget-overview-box bg-white mb-8 rounded-xl p-4 relative" style="box-shadow: 0px 8px 30px rgba(59, 56, 109, 0.07); max-width: 350px">
                                <span class="overview-title"> CONVERSATION RATE </span>
                                <div class="flex justify-between">
                                    <div class="flex justify-between items-center">
                                        <div class="flex justify-center items-center h-8 w-20 rounded p-2 mr-4" style="background-color: #fc6161; box-shadow: 0px 6px 20px rgba(252, 97, 97, 0.3)">
                                            <i class="pi pi-arrow-down w-8"></i>
                                            <span class="leading-tight">0.6%</span>
                                        </div>
                                        <div class="leading-loose text-4xl">0.81%</div>
                                    </div>
                                </div>
                                <img class="absolute" style="bottom: 14px; right: 12px" src="/demo/images/ecommerce-dashboard/rate.svg" />
                            </div>

                            <div class="widget-overview-box bg-white mb-8 rounded-xl p-4 relative" style="box-shadow: 0px 8px 30px rgba(59, 56, 109, 0.07); max-width: 350px">
                                <span class="overview-title"> AVG. ORDER VALUE </span>
                                <div class="flex justify-between">
                                    <div class="flex justify-between items-center">
                                        <div class="flex justify-center items-center h-8 w-20 rounded p-2 mr-4" style="margin-right: 12px; background-color: #0bd18a; box-shadow: 0px 6px 20px rgba(11, 209, 138, 0.3)">
                                            <i class="pi pi-arrow-up w-8"></i>
                                            <span class="leading-tight">4,2%</span>
                                        </div>
                                        <div class="leading-loose text-4xl">$306.2</div>
                                    </div>
                                </div>
                                <img class="absolute" style="bottom: 14px; right: 12px" src="/demo/images/ecommerce-dashboard/value.svg" />
                            </div>

                            <div class="widget-overview-box bg-white mb-8 rounded-xl p-4 relative" style="box-shadow: 0px 8px 30px rgba(59, 56, 109, 0.07); max-width: 350px">
                                <span class="overview-title"> ORDER QUANTITY </span>
                                <div class="flex justify-between">
                                    <div class="flex justify-between items-center">
                                        <div class="flex justify-center items-center h-8 w-20 rounded p-2 mr-4" style="background-color: #00d0de; box-shadow: 0px 6px 20px rgba(0, 208, 222, 0.3)">
                                            <i class="pi pi-minus w-8"></i>
                                            <span class="leading-tight">2,1%</span>
                                        </div>
                                        <div class="leading-loose text-4xl">1,620</div>
                                    </div>
                                </div>
                                <img class="absolute" style="bottom: 14px; right: 12px" src="/demo/images/ecommerce-dashboard/quantity.svg" />
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-12 gap-4 flex justify-between feature-boxes feature-boxes-2" style="margin-bottom: 140px; margin-left: -100px">
                        <div class="col-span-12 md:col-span-6 flex flex-row-reverse">
                            <div class="card mr-4 customer-box text-center rounded bg-white" style="box-shadow: 0px 8px 30px rgba(68, 72, 109, 0.07); max-width: 180px; max-height: 210px">
                                <div class="customer-item-content">
                                    <div class="mb-4">
                                        <img src="/demo/images/ecommerce-dashboard/beats.png" alt="beats" width="97" />
                                    </div>
                                    <div>
                                        <h4 class="p-m-1 font-medium text-xl whitespace-nowrap">9,395 Users</h4>
                                        <h5 class="mt-0 font-medium text-xl text-gray-400">$7,927,105</h5>
                                    </div>
                                </div>
                            </div>
                            <div class="card mr-4 customer-box text-center rounded bg-white" style="box-shadow: 0px 8px 30px rgba(68, 72, 109, 0.07); max-width: 180px; max-height: 210px">
                                <div class="customer-item-content">
                                    <div class="mb-4">
                                        <img src="/demo/images/ecommerce-dashboard/nasa.png" alt="nasa" width="97" />
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-xl whitespace-nowrap">9,673 Users</h4>
                                        <h5 class="mt-0 font-medium text-xl text-gray-400">$8,362,478</h5>
                                    </div>
                                </div>
                            </div>
                            <div class="card mr-4 customer-box text-center rounded bg-white" style="box-shadow: 0px 8px 30px rgba(68, 72, 109, 0.07); max-width: 180px; max-height: 210px; opacity: 0.5">
                                <div class="customer-item-content">
                                    <div class="mb-4">
                                        <img src="/demo/images/ecommerce-dashboard/north.png" alt="north-face" width="97" />
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-xl whitespace-nowrap">7,613 Users</h4>
                                        <h5 class="mt-0 font-medium text-xl text-gray-400">$5,697,883</h5>
                                    </div>
                                </div>
                            </div>
                            <div class="card mr-4 customer-box text-center rounded bg-white" style="box-shadow: 0px 8px 30px rgba(68, 72, 109, 0.07); max-width: 180px; max-height: 210px; opacity: 0.3">
                                <div class="customer-item-content">
                                    <div class="mb-4">
                                        <img src="/demo/images/ecommerce-dashboard/gopro.png" alt="go-pro" width="97" height="97" />
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-xl whitespace-nowrap">7,813 Users</h4>
                                        <h5 class="mt-0 font-medium text-xl text-gray-400">$6,471,594</h5>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-span-12 md:col-span-6">
                            <h3 class="font-medium text-3xl text-gray-900 mb-4">Curabitur ullamcorper molesti</h3>
                            <p>
                                Proin maximus sem non congue ultricies. Aenean porttitor nulla suscipit, laoreet nunc eget, pharetra felis. Etiam ac velit sit amet metus tristique ultrices. Interdum et malesuada fames ac ante ipsum primis in
                                faucibus. Vestibulum placerat nunc vitae ipsum bibendum pulvinar.
                            </p>
                        </div>
                    </div>

                    <div class="grid grid-cols-12 gap-4 feature-boxes feature-boxes-3" style="margin-bottom: 120px">
                        <div class="col-span-12 md:col-span-6">
                            <span class="text-gray-900 font-semibold text-2xl">Curabitur ullamcorper molesti</span>
                            <ul class="list-disc pl-6 mt-4">
                                <li class="text-xl">Donec ac justo vitae lorem vehicula lobortis.</li>
                                <li class="text-xl">Aenean nibh ante, auctor in faucibus id</li>
                                <li class="text-xl">Orci varius natoque penatibus et magnis</li>
                                <li class="text-xl">Ut et dapibus mauris.</li>
                                <li class="text-xl">Fusce aliquet eget nisl sed imperdiet.</li>
                            </ul>
                        </div>
                        <div class="col-span-12 md:col-span-6 feature-widgets relative">
                            <img src="/demo/images/landing/chart-widget.png" alt="atlantis" class="chart-widget" style="max-height: 260px; opacity: 0.6" />
                            <img src="/demo/images/landing/progressbar-widget.png" alt="atlantis" class="progressbar-widget absolute right-0" style="top: -45px; max-width: 350px" />
                        </div>
                    </div>
                </div>

                <div ref="pricing" id="pricing" class="flex pricing flex-col pr-20" style="padding-left: 14rem; margin-bottom: 8.5rem">
                    <h2 class="text-gray-900 font-medium text-3xl">Pricing</h2>
                    <p class="text-2xl mt-6" style="max-width: 650px; margin-bottom: 4.5rem">
                        Proin maximus sem non congue ultricies. Aenean porttitor nulla suscipit, laoreet nunc eget, pharetra felis. Etiam ac velit sit amet metus tristique ultrices. Interdum et malesuada fames ac ante ipsum primis in faucibus.
                    </p>

                    <div class="grid grid-cols-12 gap-4 pricing-content w-full">
                        <div class="col-span-12 lg:col-span-4">
                            <div class="card p-0 mr-12 h-full bg-white w-full" style="border-radius: 20px; box-shadow: 0px 10px 50px rgba(29, 15, 57, 0.13)">
                                <div class="flex flex-col items-center p-8">
                                    <span class="type font-medium text-3xl">Basic</span>
                                    <h1 class="font-medium" style="font-size: 50px">$5</h1>
                                </div>
                                <ul class="options py-0 px-8 mt-0">
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Responsive Layout</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Unlimited Push Messages</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">50 Support Ticket</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Free Shipping</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">10GB Storage</li>
                                </ul>
                                <div class="flex items-center justify-center">
                                    <Button class="buy-button !bg-gray-200 !text-gray-700 !font-semibold !py-2" severity="secondary" text outlined label="Buy now"> </Button>
                                </div>
                            </div>
                        </div>
                        <div class="col-span-12 lg:col-span-4">
                            <div class="card p-0 mr-12 h-full bg-white w-full" style="border-radius: 20px; box-shadow: 0px 10px 50px rgba(29, 15, 57, 0.13)">
                                <div class="flex flex-col items-center p-8">
                                    <span class="type font-medium text-3xl">Standart</span>
                                    <h1 class="font-medium" style="font-size: 50px">$25</h1>
                                </div>
                                <ul class="options py-0 px-8 mt-0">
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Responsive Layout</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Unlimited Push Messages</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">50 Support Ticket</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Free Shipping</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">10GB Storage</li>
                                </ul>
                                <div class="flex items-center justify-center">
                                    <Button class="active-buy-button !bg-cyan-500 !text-white !py-2 !font-semibold" severity="secondary" text outlined label="Buy now"> </Button>
                                </div>
                            </div>
                        </div>
                        <div class="col-span-12 lg:col-span-4 pricing-box pricing-professional">
                            <div class="card p-0 mr-12 h-full bg-white w-full" style="border-radius: 20px; box-shadow: 0px 10px 50px rgba(29, 15, 57, 0.13)">
                                <div class="flex flex-col items-center p-8">
                                    <span class="type font-medium text-3xl">Professional</span>
                                    <h1 class="font-medium" style="font-size: 50px">$50</h1>
                                </div>
                                <ul class="options py-0 px-8 mt-0 text-center">
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Responsive Layout</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Unlimited Push Messages</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">50 Support Ticket</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">Free Shipping</li>
                                    <li class="flex items-center justify-center text-xl p-2 text-center">10GB Storage</li>
                                </ul>
                                <div class="flex items-center justify-center">
                                    <Button class="buy-button !bg-gray-200 !text-gray-700 !font-semibold !py-2" severity="secondary" text outlined label="Buy now"> </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="footer" class="footer">
                    <div class="flex items-center justify-between py-6" style="mix-blend-mode: multiply">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center cursor-pointer" @click="goHome">
                                <img src="/layout/images/logo/logo-dark.png" alt="atlantis-layout" class="logo" style="height: 32px" />
                                <img src="/layout/images/logo/appname-dark.png" alt="atlantis-layout" class="appname ml-2" style="height: 12px" />
                                <span class="text-gray-700 opacity-70" style="margin-left: 2.5rem">Copyright - PrimeTek</span>
                            </div>
                        </div>
                        <div class="footer-right-elements flex items-center justify-between">
                            <a class="contact-icons cursor-pointer">
                                <i class="pi pi-github text-gray-700 hover:text-gray-900 mr-4 !text-xl"></i>
                            </a>

                            <a class="contact-icons cursor-pointer">
                                <i class="pi pi-twitter text-gray-700 hover:text-gray-900 mr-4 !text-xl"></i>
                            </a>
                        </div>
                    </div>

                    <div class="flex items-center pt-8">
                        <div class="newsletter">
                            <span class="header font-medium text-xl opacity-60">Newsletter</span>
                            <p class="font-medium opacity-60 mb-4">Join our newsletter to get notification about the new features</p>
                            <InputGroup>
                                <InputText type="text" placeholder="Enter your email adress" />
                                <Button class="join-button !bg-slate-500" severity="secondary" text outlined label="Join" style="mix-blend-mode: multiply; border-radius: 0 8px 8px 0"> </Button>
                            </InputGroup>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.landing-container {
    #header {
        #menu {
            display: flex;
            align-items: center;
            flex-direction: row;
            list-style-type: none;
        }
        .header-features {
            .header-feature-box {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(0, 0, 0, 0.15);
                box-sizing: border-box;
                backdrop-filter: blur(40px);
                border-radius: 20px;
                padding: 30px 33px 36px 33px;
                max-width: 370px;

                .title {
                    display: block;
                    font-size: 20px;
                    line-height: 23px;
                }

                .content {
                    font-size: 14px;
                    line-height: 16px;
                }
            }
        }
    }
    .landing-wrapper-back {
        margin-top: calc(((100vw * 0.09719) * -1) - 300px);
        padding: calc((100vw * 0.09719) * 4) - ((100vw * 0.09719) - (100vw * 0.09719)) 0 4em;
    }

    .landing-wrapper {
        #footer {
            .newsletter {
                input {
                    background: #efeffb;
                    mix-blend-mode: multiply;
                    opacity: 0.8;
                    color: #44486d;
                    border-radius: 8px 0 0 8px;
                    border-color: transparent;
                    padding: 0.714rem 1rem;
                    min-width: 400px;

                    &::placeholder {
                        font-weight: 500;
                        font-size: 14px;
                        line-height: 17px;
                        color: #44486d;
                        mix-blend-mode: multiply;
                        opacity: 0.25;
                    }
                }
            }
        }
    }
}

@media screen and (max-width: 991px) {
    .landing-container {
        #header {
            .header-features,
            .header-text {
                padding: 100px 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
        }

        #meet-atlantis {
            min-height: 430px !important;

            .ellipsis-1,
            .ellipsis-2,
            .ellipsis-3,
            .ellipsis-4 {
                display: none;
            }
        }

        .landing-wrapper-back {
            display: none;
        }

        .landing-wrapper {
            padding: 2.5rem 3rem !important;

            &.clip-path {
                clip-path: none;
                margin-top: 0;
            }

            #features {
                padding-left: 0 !important;
                padding-right: 0 !important;

                .feature-boxes {
                    &.feature-boxes-1,
                    &.feature-boxes-2,
                    &.feature-boxes-3 {
                        margin-bottom: 50px !important;
                        margin-left: 0px !important;
                    }

                    &.feature-boxes-3 {
                        .feature-widgets {
                            overflow: hidden !important;

                            .progressbar-widget {
                                max-width: 350px !important;
                                position: absolute;
                                right: -150px;
                                top: -15px;
                            }
                        }
                    }
                }
            }

            #pricing {
                padding-left: 0 !important;
                padding-right: 0 !important;

                .pricing-content {
                    .card {
                        margin-right: 0 !important;
                    }
                }
            }

            #footer {
                .newsletter {
                    p,
                    input {
                        min-width: auto;
                        max-width: 300px;
                    }
                }
            }
        }
    }
}

.clip-path {
    position: relative;
    margin-top: calc(((100vw * 0.09719) * -1) - 300px);
    padding: calc((100vw * 0.09719) * 4) - ((100vw * 0.09719) - (100vw * 0.09719)) 0 4em;
    clip-path: polygon(0% 18%, 100% 0%, 100% 100%, 0% 100%);
    -webkit-clip-path: polygon(0% 18%, 100% 0%, 100% 100%, 0% 100%);
}

@media screen and (min-width: 1960px) {
    .landing-container {
        .header-menu-container,
        .header-text,
        .header-features,
        .landing-back,
        .features,
        .pricing,
        .footer {
            width: 1504px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }
}
</style>
